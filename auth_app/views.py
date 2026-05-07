from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta, datetime, time
from .models import User, Profile, DoctorProfile
from .forms import UserRegistrationForm, ProfileForm, DoctorProfileForm, CustomAuthenticationForm, UserUpdateForm
from .mixins import PatientRequiredMixin, DoctorRequiredMixin, AdminRequiredMixin
from django.contrib.auth import login, get_backends


class CustomLoginView(LoginView):
    """Custom login view with our own template and form."""
    form_class = CustomAuthenticationForm
    template_name = 'auth/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_admin():
            return reverse_lazy('admin_dashboard')
        elif user.is_doctor():
            return reverse_lazy('doctor_dashboard')
        else:
            return reverse_lazy('patient_dashboard')


class CustomLogoutView(LogoutView):
    next_page = 'home'


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'auth/register.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        Profile.objects.create(user=user)
        if user.role == User.Role.DOCTOR:
            DoctorProfile.objects.create(user=user)
        backend = get_backends()[0]
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        login(self.request, user)
        if user.is_doctor():
            messages.success(self.request, "Registration successful! Please complete your doctor profile.")
            return HttpResponseRedirect(reverse_lazy('update_doctor_profile'))
        else:
            messages.success(self.request, "Registration successful!")
            return HttpResponseRedirect(reverse_lazy('patient_dashboard'))

    def form_invalid(self, form):
        messages.error(self.request, "Registration failed. Please correct the errors below.")
        return super().form_invalid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'auth/edit_profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)


class DoctorProfileUpdateView(LoginRequiredMixin, DoctorRequiredMixin, UpdateView):
    model = DoctorProfile
    form_class = DoctorProfileForm
    template_name = 'auth/update_doctor_profile.html'
    success_url = reverse_lazy('doctor_dashboard')

    def get_object(self, queryset=None):
        profile, _ = DoctorProfile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, "Doctor profile updated successfully!")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'auth/profile.html'
    context_object_name = 'user'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        if self.request.user.is_doctor():
            doctor_profile, _ = DoctorProfile.objects.get_or_create(user=self.request.user)
            context['doctor_profile'] = doctor_profile
        return context


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------

def _sparkline_points(values, width=100, height=32):
    """Convert a list of ints into an SVG polyline `points` string."""
    if not values:
        return ""
    n = len(values)
    vmax = max(values) or 1
    if n == 1:
        return f"0,{height // 2} {width},{height // 2}"
    step = width / (n - 1)
    pts = []
    for i, v in enumerate(values):
        x = i * step
        y = height - (v / vmax) * (height - 4) - 2
        pts.append(f"{x:.1f},{y:.1f}")
    return " ".join(pts)


class PatientDashboardView(LoginRequiredMixin, PatientRequiredMixin, TemplateView):
    """Patient dashboard — care timeline."""
    template_name = 'patient/dashboard.html'

    def get_context_data(self, **kwargs):
        from consultation_app.models import Appointment, HealthTip
        from auth_app.models import DoctorProfile

        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        today = now.date()

        # Base queryset; select_related pulls doctor in same query.
        # prefetch_related pulls all OneToOne / reverse FK artefacts in O(1) extra
        # queries (4 small extras) instead of O(N) per row in the template.
        appts = (Appointment.objects
                 .filter(patient=user)
                 .select_related('doctor', 'doctor__doctor_profile'))

        # An appointment is considered "past" / "done" if any of:
        #   * scheduled time has passed
        #   * status is terminal (COMPLETED / CANCELLED / NO_SHOW)
        #   * a Transcription exists for it (a call actually ended)
        # This keeps the timeline accurate even when calls end before the
        # scheduled slot, or are tested with future dates.
        terminal_statuses = [
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
            Appointment.Status.NO_SHOW,
        ]
        past_q = (
            Q(appointment_date__lt=today)
            | Q(appointment_date=today, appointment_time__lt=now.time())
            | Q(status__in=terminal_statuses)
            | Q(transcription__isnull=False)
        )

        upcoming = (appts
                    .exclude(past_q)
                    .order_by('appointment_date', 'appointment_time'))

        next_appt = upcoming.first()

        past = (appts
                .filter(past_q)
                .order_by('-appointment_date', '-appointment_time')
                .prefetch_related('transcription', 'soap_note', 'follow_up', 'prescriptions')
                .distinct()
                [:20])

        # Aggregate counts in a single DB hit instead of two separate count() calls
        from django.db.models import Count
        agg = appts.aggregate(
            upcoming_count=Count('id', filter=~past_q, distinct=True),
            completed_count=Count('id', filter=Q(status=Appointment.Status.COMPLETED), distinct=True),
        )

        context['next_appt'] = next_appt
        context['upcoming_count'] = agg['upcoming_count'] or 0
        context['past_appts'] = past
        context['completed_count'] = agg['completed_count'] or 0

        if next_appt:
            slot_dt = timezone.make_aware(datetime.combine(next_appt.appointment_date, next_appt.appointment_time))
            delta = slot_dt - now
            context['next_appt_delta'] = delta
            context['next_appt_seconds'] = max(int(delta.total_seconds()), 0)

        # Empty-state discovery: featured doctors
        if not next_appt:
            context['featured_doctors'] = (DoctorProfile.objects
                                           .filter(is_available=True)
                                           .select_related('user')[:6])

        context['health_tips'] = HealthTip.objects.filter(is_featured=True)[:3]
        return context


class DoctorDashboardView(LoginRequiredMixin, DoctorRequiredMixin, TemplateView):
    """Doctor dashboard — operational cockpit."""
    template_name = 'doctor/dashboard.html'

    def get_context_data(self, **kwargs):
        from consultation_app.models import Appointment, Availability, Prescription, FollowUp
        from transcription_app.models import SOAPNote

        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        today = now.date()

        appts = (Appointment.objects
                 .filter(doctor=user)
                 .select_related('patient'))

        # Show all of today's non-cancelled appointments in the queue (so the
        # doctor sees the full day's roster, including already-done ones with
        # COMPLETED status pill). Prefetch transcription so per-row "is done?"
        # checks below don't N+1.
        today_appts = (appts
                       .filter(appointment_date=today)
                       .exclude(status=Appointment.Status.CANCELLED)
                       .prefetch_related('transcription')
                       .order_by('appointment_time'))

        terminal_statuses = (
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
            Appointment.Status.NO_SHOW,
        )

        def _is_done(appt):
            """An appointment is done if status is terminal OR a Transcription exists."""
            if appt.status in terminal_statuses:
                return True
            # hasattr safely catches RelatedObjectDoesNotExist for OneToOne reverse
            return hasattr(appt, 'transcription')

        # Now / Next — skip already-done appointments
        current_t = now.time()
        now_appt = next(
            (a for a in today_appts
             if a.status == Appointment.Status.CONFIRMED
             and a.appointment_time <= current_t
             and not _is_done(a)),
            None,
        )
        upcoming_today = [a for a in today_appts
                          if a.appointment_time > current_t and not _is_done(a)]
        next_appt = upcoming_today[0] if upcoming_today else None

        if not next_appt:
            future = (appts
                      .filter(appointment_date__gt=today)
                      .exclude(status__in=terminal_statuses)
                      .order_by('appointment_date', 'appointment_time')
                      .first())
            next_appt = future

        context['now_appt'] = now_appt
        context['next_appt'] = next_appt
        context['today_appts'] = today_appts

        # Action inbox: completed without prescription, SOAP awaiting attention, follow-ups to schedule
        completed = appts.filter(status=Appointment.Status.COMPLETED)

        prescription_appt_ids = set(Prescription.objects
                                    .filter(appointment__doctor=user)
                                    .values_list('appointment_id', flat=True))
        followup_appt_ids = set(FollowUp.objects
                                .filter(appointment__doctor=user)
                                .values_list('appointment_id', flat=True))

        rx_pending = [a for a in completed if a.id not in prescription_appt_ids][:6]
        followup_pending = [a for a in completed
                            if a.id not in followup_appt_ids
                            and a.id in prescription_appt_ids][:6]

        soap_pending = (SOAPNote.objects
                        .filter(appointment__doctor=user, is_edited=False,
                                status=SOAPNote.Status.COMPLETED)
                        .select_related('appointment', 'appointment__patient')[:6])

        context['rx_pending'] = rx_pending
        context['followup_pending'] = followup_pending
        context['soap_pending'] = soap_pending
        context['inbox_count'] = len(rx_pending) + len(followup_pending) + soap_pending.count()

        # 7-day availability heat map
        end = today + timedelta(days=6)
        slots = (Availability.objects
                 .filter(doctor=user, date__gte=today, date__lte=end)
                 .order_by('date', 'start_time'))
        days = []
        for i in range(7):
            d = today + timedelta(days=i)
            day_slots = [s for s in slots if s.date == d]
            days.append({
                'date': d,
                'is_today': d == today,
                'slots': day_slots,
                'open': sum(1 for s in day_slots if not s.is_booked),
                'booked': sum(1 for s in day_slots if s.is_booked),
            })
        context['availability_days'] = days

        # Bottom metrics
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        context['metric_week_sessions'] = appts.filter(
            status=Appointment.Status.COMPLETED,
            appointment_date__gte=week_start
        ).count()
        context['metric_month_sessions'] = appts.filter(
            status=Appointment.Status.COMPLETED,
            appointment_date__gte=month_start
        ).count()
        context['metric_unique_patients'] = appts.values('patient').distinct().count()
        fee = getattr(getattr(user, 'doctor_profile', None), 'consultation_fee', 0) or 0
        context['metric_month_earnings'] = int(fee) * context['metric_month_sessions']

        return context


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin dashboard — mission control."""
    template_name = 'admin/dashboard.html'

    def get_context_data(self, **kwargs):
        from consultation_app.models import Appointment
        from payment_app.models import Payment
        from transcription_app.models import Transcription

        context = super().get_context_data(**kwargs)
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=6)
        prev_week_ago = today - timedelta(days=13)

        # User counts
        total_users = User.objects.count()
        total_doctors = User.objects.filter(role=User.Role.DOCTOR).count()
        total_patients = User.objects.filter(role=User.Role.PATIENT).count()
        total_admins = User.objects.filter(role=User.Role.ADMIN).count()
        new_users_24h = User.objects.filter(date_joined__gte=now - timedelta(days=1)).count()
        new_users_week = User.objects.filter(date_joined__gte=now - timedelta(days=7)).count()
        new_users_prev_week = User.objects.filter(
            date_joined__gte=now - timedelta(days=14),
            date_joined__lt=now - timedelta(days=7)
        ).count()
        active_doctors = DoctorProfile.objects.filter(is_available=True).count()

        # Appointments
        appts_today = Appointment.objects.filter(appointment_date=today).count()
        appts_today_confirmed = Appointment.objects.filter(
            appointment_date=today, status=Appointment.Status.CONFIRMED
        ).count()
        appts_week = Appointment.objects.filter(appointment_date__gte=week_ago).count()
        appts_prev_week = Appointment.objects.filter(
            appointment_date__gte=prev_week_ago, appointment_date__lt=week_ago
        ).count()

        # Revenue (real)
        completed_payments = Payment.objects.filter(status=Payment.Status.COMPLETED)
        total_revenue = completed_payments.aggregate(s=Sum('amount'))['s'] or 0
        week_revenue = completed_payments.filter(
            created_at__gte=now - timedelta(days=7)
        ).aggregate(s=Sum('amount'))['s'] or 0
        prev_week_revenue = completed_payments.filter(
            created_at__gte=now - timedelta(days=14),
            created_at__lt=now - timedelta(days=7)
        ).aggregate(s=Sum('amount'))['s'] or 0
        payments_count = completed_payments.count()

        # Sparkline series (last 7 days) — 3 GROUP-BY queries instead of 21 COUNTs.
        from django.db.models.functions import TruncDate
        from django.db.models import Count

        seven_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

        def _series_from_groupby(qs, date_field, value_expr=None):
            """qs grouped by TruncDate(date_field). Returns dict {date: count|sum}."""
            qs = qs.annotate(_d=TruncDate(date_field)).values('_d')
            qs = qs.annotate(_v=value_expr) if value_expr is not None else qs.annotate(_v=Count('id'))
            return {row['_d']: row['_v'] for row in qs}

        users_map = _series_from_groupby(
            User.objects.filter(date_joined__date__gte=seven_days[0]),
            'date_joined',
        )
        appts_map = _series_from_groupby(
            Appointment.objects.filter(appointment_date__gte=seven_days[0]),
            'appointment_date',
        )
        revenue_map = _series_from_groupby(
            completed_payments.filter(created_at__date__gte=seven_days[0]),
            'created_at',
            value_expr=Sum('amount'),
        )

        signups_series = [users_map.get(d, 0) for d in seven_days]
        appts_series = [appts_map.get(d, 0) for d in seven_days]
        revenue_series = [int(revenue_map.get(d, 0) or 0) for d in seven_days]
        active_series = [active_doctors] * 7  # static line

        context['spark_users'] = _sparkline_points(signups_series)
        context['spark_appts'] = _sparkline_points(appts_series)
        context['spark_revenue'] = _sparkline_points(revenue_series)
        context['spark_doctors'] = _sparkline_points(active_series)

        def pct_delta(curr, prev):
            if prev == 0:
                return ("+100%", "emerald") if curr else ("0%", "slate")
            change = (curr - prev) / prev * 100
            tone = "emerald" if change >= 0 else "red"
            sign = "+" if change >= 0 else ""
            return (f"{sign}{change:.0f}% vs last week", tone)

        u_delta, u_tone = pct_delta(new_users_week, new_users_prev_week)
        a_delta, a_tone = pct_delta(appts_week, appts_prev_week)
        r_delta, r_tone = pct_delta(int(week_revenue), int(prev_week_revenue))

        context.update({
            'total_users': total_users,
            'total_doctors': total_doctors,
            'total_patients': total_patients,
            'total_admins': total_admins,
            'new_users_24h': new_users_24h,
            'new_users_week': new_users_week,
            'active_doctors': active_doctors,
            'active_doctors_label': f"{total_doctors} total",
            'appointments_today': appts_today,
            'appointments_week': appts_week,
            'appointments_confirmed': appts_today_confirmed,
            'total_revenue': int(total_revenue),
            'week_revenue': int(week_revenue),
            'week_revenue_display': f"₹{int(week_revenue):,}",
            'payments_count': payments_count,
            'users_delta': u_delta, 'users_delta_tone': u_tone,
            'appts_delta': a_delta, 'appts_delta_tone': a_tone,
            'revenue_delta': r_delta, 'revenue_delta_tone': r_tone,
        })

        # Recent users / appointments (compact)
        context['recent_users'] = User.objects.order_by('-date_joined')[:6]
        context['recent_appointments'] = (Appointment.objects
                                          .select_related('patient', 'doctor', 'payment')
                                          .order_by('-created_at')[:6])

        # Activity feed (mixed event stream, last 10 events)
        events = []
        for u in User.objects.order_by('-date_joined')[:5]:
            events.append({
                'kind': 'signup',
                'icon': 'fa-user-plus',
                'tone': 'indigo',
                'when': u.date_joined,
                'text': f"{u.get_full_name() or u.email} signed up as {u.get_role_display()}",
            })
        for a in Appointment.objects.order_by('-created_at')[:5]:
            events.append({
                'kind': 'appointment',
                'icon': 'fa-calendar-plus',
                'tone': 'violet',
                'when': a.created_at,
                'text': f"Appointment booked: {a.patient.get_full_name() or a.patient.email} → Dr. {a.doctor.get_full_name() or a.doctor.email}",
            })
        for p in completed_payments.order_by('-updated_at')[:5]:
            events.append({
                'kind': 'payment',
                'icon': 'fa-indian-rupee-sign',
                'tone': 'emerald',
                'when': p.updated_at,
                'text': f"Payment ₹{p.amount} completed for {p.patient.get_full_name() or p.patient.email}",
            })
        for t in Transcription.objects.filter(status=Transcription.Status.FAILED).order_by('-updated_at')[:3]:
            events.append({
                'kind': 'transcription_failed',
                'icon': 'fa-triangle-exclamation',
                'tone': 'red',
                'when': t.updated_at,
                'text': f"Transcription failed for appointment {str(t.appointment_id)[:8]}",
            })
        events.sort(key=lambda e: e['when'], reverse=True)
        context['activity_events'] = events[:10]

        # Issues panel
        issues = []
        failed_payments = Payment.objects.filter(status=Payment.Status.FAILED).count()
        if failed_payments:
            issues.append({'icon': 'fa-credit-card', 'tone': 'red',
                           'title': f"{failed_payments} failed payment{'s' if failed_payments > 1 else ''}",
                           'url': '/admin/payment_app/payment/?status__exact=FAILED'})

        failed_tx = Transcription.objects.filter(status=Transcription.Status.FAILED).count()
        if failed_tx:
            issues.append({'icon': 'fa-microphone-slash', 'tone': 'amber',
                           'title': f"{failed_tx} failed transcription{'s' if failed_tx > 1 else ''}",
                           'url': '/admin/transcription_app/transcription/?status__exact=FAILED'})

        no_shows = Appointment.objects.filter(status=Appointment.Status.NO_SHOW).count()
        if no_shows:
            issues.append({'icon': 'fa-user-slash', 'tone': 'amber',
                           'title': f"{no_shows} no-show appointment{'s' if no_shows > 1 else ''}",
                           'url': '/admin/consultation_app/appointment/?status__exact=NO_SHOW'})

        doctors_no_avail = (User.objects.filter(role=User.Role.DOCTOR)
                            .exclude(availabilities__date__gte=today,
                                     availabilities__date__lte=today + timedelta(days=7))
                            .count())
        if doctors_no_avail:
            issues.append({'icon': 'fa-calendar-xmark', 'tone': 'slate',
                           'title': f"{doctors_no_avail} doctor{'s' if doctors_no_avail > 1 else ''} with no upcoming availability",
                           'url': '/admin/auth_app/doctorprofile/'})

        context['issues'] = issues

        return context
