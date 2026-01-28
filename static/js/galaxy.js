const canvas = document.getElementById('starfield'); 
const ctx = canvas.getContext('2d');
let stars = [];

function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
window.addEventListener('resize', resize); resize();

function initStars() {
    stars = [];
    for(let i=0; i<150; i++) {
        stars.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 2,
            speed: Math.random() * 0.5 + 0.1
        });
    }
}

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'white';
    stars.forEach(s => {
        s.y -= s.speed;
        if(s.y < 0) s.y = canvas.height;
        ctx.globalAlpha = Math.random() * 0.5 + 0.3;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.size, 0, Math.PI*2);
        ctx.fill();
    });
    requestAnimationFrame(animate);
}

initStars();
animate();

function toggleGalaxy() {
    document.body.classList.toggle('galaxy-mode');
    document.getElementById('galaxy-btn').classList.toggle('galaxy-open');
}
