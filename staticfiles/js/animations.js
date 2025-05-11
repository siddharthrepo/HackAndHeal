/**
 * Chikitsa360 Animations
 * Custom animations for a modern healthcare experience
 */

// Scroll animation observer
document.addEventListener('DOMContentLoaded', function() {
    // Select all elements with the animate-on-scroll class
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    // Create the observer config
    const observerConfig = {
        root: null, // Use viewport as root
        threshold: 0.1, // Trigger when 10% of the element is visible
        rootMargin: '0px 0px -100px 0px' // Offset from the bottom
    };
    
    // Callback for the observer
    const observerCallback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Get the animation type from the data-animation attribute
                const animationType = entry.target.dataset.animation;
                
                // Remove opacity-0 class
                entry.target.classList.remove('opacity-0');
                
                // Add the appropriate animation class
                switch(animationType) {
                    case 'fade-in':
                        entry.target.classList.add('c360-fade-in');
                        break;
                    case 'slide-up':
                        entry.target.classList.add('c360-slide-up');
                        break;
                    case 'slide-in-right':
                        entry.target.classList.add('c360-slide-in-right');
                        break;
                    default:
                        entry.target.classList.add('c360-fade-in');
                }
                
                // Stop observing the element after it's animated
                observer.unobserve(entry.target);
            }
        });
    };
    
    // Create the observer
    const observer = new IntersectionObserver(observerCallback, observerConfig);
    
    // Observe each animated element
    animatedElements.forEach(element => {
        observer.observe(element);
    });
});

// Parallax effect for hero section
function parallaxHero() {
    const heroSection = document.querySelector('.c360-hero');
    if (!heroSection) return;
    
    const heroShapes = document.querySelectorAll('.c360-hero-shape');
    
    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;
        
        heroShapes.forEach((shape, index) => {
            // Apply different speeds based on index for multi-layer effect
            const speed = 0.05 + (index * 0.02);
            shape.style.transform = `translateY(${scrollY * speed}px)`;
        });
    });
}

// Call the parallax function
parallaxHero();

// Animate numbers incrementally (e.g., for statistics)
function animateCounters() {
    const counters = document.querySelectorAll('.c360-counter');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 2000; // 2 seconds
        const step = target / (duration / 16); // 60fps
        let current = 0;
        
        const updateCounter = () => {
            current += step;
            if (current < target) {
                counter.textContent = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        const counterObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                updateCounter();
                counterObserver.unobserve(counter);
            }
        }, { threshold: 0.5 });
        
        counterObserver.observe(counter);
    });
}

// Call the counter animation function
animateCounters();

// Smooth scroll for anchor links
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.getAttribute('href').startsWith('#')) {
        e.preventDefault();
        
        const targetId = e.target.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80, // Accounting for fixed header
                behavior: 'smooth'
            });
        }
    }
});