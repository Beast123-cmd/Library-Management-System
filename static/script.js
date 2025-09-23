// Flash messages auto-hide with fade out
document.addEventListener("DOMContentLoaded", function() {
    const flashes = document.querySelectorAll(".flash");
    flashes.forEach(f => {
        setTimeout(() => {
            f.style.transition = "opacity 0.5s ease";
            f.style.opacity = "0";
            setTimeout(() => f.remove(), 500);
        }, 4000);
    });

    // Charts (if present)
    const pieCanvas = document.getElementById("pieChart");
    if(pieCanvas) {
        new Chart(pieCanvas, {
            type: 'pie',
            data: {
                labels: JSON.parse(pieCanvas.dataset.labels),
                datasets: [{ data: JSON.parse(pieCanvas.dataset.values), backgroundColor: ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40'] }]
            },
            options: { responsive: true, animation: { animateScale: true } }
        });
    }

    const barCanvas = document.getElementById("barChart");
    if(barCanvas) {
        new Chart(barCanvas, {
            type: 'bar',
            data: {
                labels: JSON.parse(barCanvas.dataset.labels),
                datasets: [{ label: 'Number of Issues', data: JSON.parse(barCanvas.dataset.values), backgroundColor: '#36A2EB' }]
            },
            options: { responsive: true, animation: { duration: 1200, easing: 'easeOutBounce' }, scales: { y: { beginAtZero: true, precision:0 } } }
        });
    }
});

// Sidebar toggle
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('collapsed');
}

// Dark mode toggle with smooth transition
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
}
