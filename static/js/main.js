// Auto hide alerts
setTimeout(() => {
    document.querySelectorAll('.alert').forEach(a => {
        a.style.opacity = '0';
        a.style.transition = 'opacity 0.5s';
        setTimeout(() => a.remove(), 500);
    });
}, 4000);

// Active nav link
const path = window.location.pathname;
document.querySelectorAll('.nav-link').forEach(link => {
    if(link.getAttribute('href') === path) {
        link.style.background = '#e8f0fe';
        link.style.color = '#1877f2';
    }
});