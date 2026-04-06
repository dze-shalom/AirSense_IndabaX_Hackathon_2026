// Particles.js Configuration
function initializeParticles() {
    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            particles: {
                number: {
                    value: 160,
                    density: {
                        enable: true,
                        value_area: 800
                    }
                },
                color: {
                    value: "#64ffda"
                },
                shape: {
                    type: "circle",
                    stroke: {
                        width: 0,
                        color: "#000000"
                    },
                    polygon: {
                        nb_sides: 5
                    }
                },
                opacity: {
                    value: 0.1,
                    random: true,
                    anim: {
                        enable: false,
                        speed: 1,
                        opacity_min: 0.1,
                        sync: false
                    }
                },
                size: {
                    value: 3,
                    random: true,
                    anim: {
                        enable: false,
                        speed: 10,
                        size_min: 0.1,
                        sync: false
                    }
                },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: "#64ffda",
                    opacity: 0.1,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 1,
                    direction: "none",
                    random: false,
                    straight: false,
                    out_mode: "out",
                    bounce: false,
                    attract: {
                        enable: false,
                        rotateX: 600,
                        rotateY: 1200
                    }
                }
            },
            interactivity: {
                detect_on: "canvas",
                events: {
                    onhover: {
                        enable: true,
                        mode: "grab"
                    },
                    onclick: {
                        enable: true,
                        mode: "push"
                    },
                    resize: true
                },
                modes: {
                    grab: {
                        distance: 140,
                        line_linked: {
                            opacity: 0.5
                        }
                    },
                    bubble: {
                        distance: 400,
                        size: 40,
                        duration: 2,
                        opacity: 8,
                        speed: 3
                    },
                    repulse: {
                        distance: 200,
                        duration: 0.4
                    },
                    push: {
                        particles_nb: 4
                    },
                    remove: {
                        particles_nb: 2
                    }
                }
            },
            retina_detect: true
        });
    }

    // Update particles color based on theme
    updateParticlesTheme();
}

// Update particles based on theme
function updateParticlesTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    
    if (typeof pJSDom !== 'undefined' && pJSDom[0]) {
        const particleColor = currentTheme === 'dark' ? '#64ffda' : '#0891b2';
        
        // Update particle colors
        if (pJSDom[0].pJS && pJSDom[0].pJS.particles) {
            pJSDom[0].pJS.particles.color.value = particleColor;
            pJSDom[0].pJS.particles.line_linked.color = particleColor;
            
            // Update existing particles
            if (pJSDom[0].pJS.particles.array) {
                pJSDom[0].pJS.particles.array.forEach(particle => {
                    particle.color.value = particleColor;
                });
            }
        }
    }
}