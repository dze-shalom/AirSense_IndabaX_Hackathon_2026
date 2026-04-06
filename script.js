// ===== MAIN JAVASCRIPT FILE =====
// Portfolio by Dze-Kum Shalom Chow

// Global variables
let projectsData = [];
let blogData = [];
let filtersInitialized = false;
let currentLang = 'en';
let portfolioDataFr = null; // Will hold French translations

// ===== EMBEDDED DATA =====
const PORTFOLIO_DATA = {
    education: [
    {
      "year": "August 2024 - Febuary 2026",
      "degree": "M.Sc in Data Science",
      "institution": "African Institute of Mathematical Sciences (AIMS)",
      "description": "Advanced studies in machine learning, statistical modeling, data visualization, big data technologies, and artificial intelligence. Conducting research on Stochastic Random Forest modeling with applications in Data science, Agriculture, and Health.",
      "achievements": [
        "Research focus on Stochastic Random Forest applications",
        "Advanced machine learning and AI coursework",
        "Big data analytics and visualization projects",
        "Mathematical modeling and statistical analysis",
        "Internship focus on Reinforcement Learning for interllegent sampling in a precison agriculture network"
      ]
    },
    {
      "year": "November 2022 - August 2025",
      "degree": "M.Tech in Telecommunications and Network Engineering",
      "institution": "University of Buea",
      "description": "Specialized in network protocols, wireless communications, fiber optics, network security, and telecommunications infrastructure. Thesis focused on Radio Frequency Measurement and Propagation model Optimization with implications for Cellular network Planning and network design.",
      "achievements": [
        "Thesis on RF Measurement and Propagation Optimization",
        "Expertise in cellular network planning and design",
        "Advanced telecommunications and network security",
        "Wireless communication systems optimization"
      ]
    },
    {
      "year": "October 2018 - August 2022",
      "degree": "B.Eng in Electrical and Electronic Engineering",
      "institution": "University of Buea",
      "description": "Foundational studies in circuit design, digital systems, power electronics, control systems, and signal processing. Graduated with Second Class Upper honors, completing a capstone project on designing a smart water meter.",
      "achievements": [
        "Second Class Upper Division honors",
        "Smart water meter capstone project",
        "Strong foundation in circuit design and electronics",
        "Power systems and control systems expertise"
      ]
    }
  ],
    
    skillCategories: [
    {
      "name": "Engineering & Hardware",
      "icon": "fas fa-microchip",
      "skills": [
        { "name": "Circuit Design", "level": 60 },
        { "name": "AUTOCAD", "level": 50 },
        { "name": "CAD Design", "level": 40 },
        { "name": "Signal Processing", "level": 80 },
        { "name": "MATLAB", "level": 67 },
        { "name": "Electronics Design", "level": 60 }
      ]
    },
    {
      "name": "Telecommunications & Networking",
      "icon": "fas fa-wifi",
      "skills": [
        { "name": "RF Engineering", "level": 67 },
        { "name": "Fiber Optics", "level": 82 },
        { "name": "Wireless Communications", "level": 70 },
        { "name": "Network Protocols", "level": 64 }
      ]
    },
    {
      "name": "Data Science & Machine Learning",
      "icon": "fas fa-chart-line",
      "skills": [
        { "name": "Python", "level": 60 },
        { "name": "Machine Learning", "level": 75 },
        { "name": "Statistical Analysis", "level": 70 },
        { "name": "Data Visualization", "level": 90 },
        { "name": "R Programming", "level": 60 }
      ]
    },
    {
      "name": "Web Development (Full Stack)",
      "icon": "fas fa-code",
      "skills": [
        { "name": "HTML5", "level": 80 },
        { "name": "CSS3", "level": 75 },
        { "name": "JavaScript", "level": 50 },
        { "name": "React.js", "level": 55 }
      ]
    },
    {
      "name": "Mobile App Development",
      "icon": "fas fa-mobile-alt",
      "skills": [
        { "name": "React Native", "level": 60 },
        { "name": "Firebase", "level": 50 },
        { "name": "Mobile UI/UX Design", "level": 40 },
        { "name": "Material Design", "level": 86 }
      ]
    },
    {
      "name": "Tools & Technologies",
      "icon": "fas fa-tools",
      "skills": [
        { "name": "IoT Systems", "level": 88 },
        { "name": "Arduino", "level": 90 },
        { "name": "ESP8266/ESP32", "level": 87 },
        { "name": "MATLAB", "level": 87 },
        { "name": "AUTOCAD", "level": 88 },
        { "name": "Linux", "level": 82 },
        { "name": "Version Control (Git)", "level": 90 },
        { "name": "Jupyter Notebooks", "level": 89 },
        { "name": "VS Code", "level": 93 },
      ]
    },
    {
      "name": "Soft Skills & Languages",
      "icon": "fas fa-users",
      "skills": [
        { "name": "Problem Solving", "level": 93 },
        { "name": "Project Management", "level": 85 },
        { "name": "Team Leadership", "level": 82 },
        { "name": "Technical Writing", "level": 88 },
        { "name": "Public Speaking", "level": 80 },
        { "name": "English", "level": 95 },
        { "name": "French", "level": 10 },
        { "name": "Research & Analysis", "level": 91 },
        { "name": "Critical Thinking", "level": 89 }
      ]
    }
  ],
    
    projects: [
        {
            "id": 1,
            "title": "Smart Farm Monitoring System",
            "category": "engineering",
            "image": "assets/images/projects/engineering/smart-farm.png",
            "description": "IoT-based agricultural automation solution that monitors environmental conditions and automates irrigation. Using ESP8266 microcontroller with multiple sensors, the system achieved 98.5% reliable sensor readings and reduced water usage by 30%.",
            "technologies": ["IoT", "Arduino", "ESP8266", "C++", "HTML", "CSS", "JavaScript", "Sensors", "MQTT"],
            "github": "https://github.com/dze-shalom/smart-farm-system",
            "live": null
        },
        {
            "id": 2,
            "title": "Blood Donation Eligibility Prediction",
            "category": "data-science",
            "image": "assets/images/projects/data-science/blood-donation.png",
            "description": "A machine learning system to predict blood donation eligibility, classifying donors as Eligible, Temporarily Non-eligible, or Permanently Non-eligible. Built using RandomForest (88.75% accuracy).",
            "technologies": ["Python", "Scikit-learn", "SMOTE", "Streamlit", "SHAP", "FastAPI", "Machine Learning"],
            "github": "https://github.com/dze-shalom/Blood-Donation",
            "live": null
        },
        {
            "id": 3,
            "title": "Crop Recommendation System",
            "category": "data-science",
            "image": "assets/images/projects/data-science/crop-recommendation.png",
            "description": "Machine learning-powered crop recommendation system that analyzes soil conditions, weather patterns, and environmental factors to suggest optimal crops for farmers.",
            "technologies": ["Python", "Machine Learning", "Pandas", "Scikit-learn", "Flask", "NumPy"],
            "github": "https://github.com/dze-shalom/Crop-Recommendation",
            "live": null
        },
        {
            "id": 4,
            "title": "Customer Churn Analysis",
            "category": "data-science",
            "image": "assets/images/projects/data-science/customer-churn.png",
            "description": "Machine learning application to predict customer churn in the telecom industry. Using a dataset of 7,043 customers, the Random Forest model achieved 85% ROC-AUC score.",
            "technologies": ["Python", "Pandas", "Scikit-learn", "Matplotlib", "Seaborn", "Random Forest"],
            "github": "https://github.com/dze-shalom/Chunk-Analysis",
            "live": null
        },
        {
            "id": 5,
            "title": "MUFEPREC Website",
            "category": "web-development",
            "image": "assets/images/projects/web-development/mufeprec-website.jpeg",
            "description": "Full-stack school platform built with HTML,Css and Javascript frontend and Node.js backend. Features include user authentication, product catalog, shopping cart, and payment integration.",
            "technologies": ["HTML", "CSS", "Javascript","Node.js"],
            "github": "https://github.com/dze-shalom/MUFEPREC-WEBSITE",
            "live": "https://mufeprecweb.netlify.app/"
        },
       
   
        {
            "id": 6,
            "title": "Portfolio Website",
            "category": "web-development",
            "image": "assets/images/projects/web-development/portfolio-website.jpg",
            "description": "Modern, responsive portfolio website built with vanilla HTML5, CSS3, and JavaScript. Features dark/light theme toggle and smooth animations.",
            "technologies": ["HTML5", "CSS3", "JavaScript", "Particles.js", "Responsive Design"],
            "github": "https://github.com/dze-shalom/MyPortfolio",
            "live": "https://dzekumshalom.netlify.app/"
        },
        {
            "id": 7,
            "title": "AgriBot - Agriculture AI Assistant",
            "category": "data-science",
            "image": "assets/images/projects/data-science/agribot.png",
            "description": "AI-powered chatbot specialized in agriculture, providing answers to farming questions, disease analysis through image recognition, and location-based planting advice. Helps farmers make data-driven decisions for better crop yields.",
            "technologies": ["Python", "Machine Learning", "Flask","HTML","Taiwland CSS","JavaScript", "NLP", "TensorFlow", "OpenCV", "Geolocation API","PostgreSQL"],
            "github": "https://github.com/dze-shalom/agribot",
            "live": "https://agribot-1-ed6c.onrender.com"
        }
    ],


};

// ===== FRENCH PORTFOLIO DATA =====
const PORTFOLIO_DATA_FR = {
    education: [
        {
            "year": "2024 - présent",
            "degree": "M.Sc en Science des Données",
            "institution": "Institut Africain des Sciences Mathématiques (AIMS)",
            "description": "Études avancées en apprentissage automatique, modélisation statistique, visualisation de données, technologies de big data et intelligence artificielle. Mène des recherches sur la modélisation Stochastique Random Forest avec des applications en Science des données, Agriculture et Santé.",
            "achievements": [
                "Focus de recherche sur les applications Stochastiques Random Forest",
                "Cursus avancé en apprentissage automatique et IA",
                "Projets d'analytique et visualisation de big data",
                "Modélisation mathématique et analyse statistique"
            ]
        },
        {
            "year": "2022 - 2025",
            "degree": "M.Tech en Télécommunications et Ingénierie Réseau",
            "institution": "Université de Buéa",
            "description": "Spécialisé dans les protocoles réseau, communications sans fil, fibre optique, sécurité réseau et infrastructure de télécommunications. Thèse axée sur la mesure de fréquence radio et l'optimisation des modèles de propagation avec des implications pour la planification de réseau cellulaire et la conception de réseau.",
            "achievements": [
                "Thèse sur la mesure RF et l'optimisation de la propagation",
                "Expertise en planification et conception de réseau cellulaire",
                "Télécommunications avancées et sécurité réseau",
                "Optimisation des systèmes de communication sans fil"
            ]
        },
        {
            "year": "2018 - 2022",
            "degree": "B.Eng en Génie Électrique et Électronique",
            "institution": "Université de Buéa",
            "description": "Études fondamentales en conception de circuits, systèmes numériques, électronique de puissance, systèmes de contrôle et traitement du signal. Diplômé avec mention Deuxième Classe Supérieure, complétant un projet de fin d'études sur la conception d'un compteur d'eau intelligent.",
            "achievements": [
                "Mention Deuxième Classe Division Supérieure",
                "Projet de fin d'études : compteur d'eau intelligent",
                "Solide fondation en conception de circuits et électronique",
                "Expertise en systèmes électriques et systèmes de contrôle"
            ]
        }
    ],
    projects: [
        {
            "id": 1,
            "title": "Système de Surveillance de Ferme Intelligente",
            "category": "engineering",
            "image": "assets/images/projects/engineering/smart-farm.png",
            "description": "Solution d'automatisation agricole basée sur l'IoT qui surveille les conditions environnementales et automatise l'irrigation. Utilisant un microcontrôleur ESP8266 avec plusieurs capteurs, le système a atteint 98,5% de fiabilité de lecture des capteurs et réduit la consommation d'eau de 30%.",
            "technologies": ["IoT", "Arduino", "ESP8266", "C++", "HTML", "CSS", "JavaScript", "Capteurs", "MQTT"],
            "github": "https://github.com/dze-shalom/smart-farm-system",
            "live": null
        },
        {
            "id": 2,
            "title": "Prédiction d'Éligibilité au Don de Sang",
            "category": "data-science",
            "image": "assets/images/projects/data-science/blood-donation.png",
            "description": "Un système d'apprentissage automatique pour prédire l'éligibilité au don de sang, classant les donneurs comme Éligibles, Temporairement Non-éligibles ou Définitivement Non-éligibles. Construit avec RandomForest (88,75% de précision).",
            "technologies": ["Python", "Scikit-learn", "SMOTE", "Streamlit", "SHAP", "FastAPI", "Machine Learning"],
            "github": "https://github.com/dze-shalom/Blood-Donation",
            "live": null
        },
        {
            "id": 3,
            "title": "Système de Recommandation de Cultures",
            "category": "data-science",
            "image": "assets/images/projects/data-science/crop-recommendation.png",
            "description": "Système de recommandation de cultures alimenté par l'apprentissage automatique qui analyse les conditions du sol, les modèles météorologiques et les facteurs environnementaux pour suggérer des cultures optimales aux agriculteurs.",
            "technologies": ["Python", "Machine Learning", "Pandas", "Scikit-learn", "Flask", "NumPy"],
            "github": "https://github.com/dze-shalom/Crop-Recommendation",
            "live": null
        },
        {
            "id": 4,
            "title": "Analyse du Taux d'Attrition Client",
            "category": "data-science",
            "image": "assets/images/projects/data-science/customer-churn.png",
            "description": "Application d'apprentissage automatique pour prédire l'attrition des clients dans l'industrie des télécommunications. Utilisant un ensemble de données de 7 043 clients, le modèle Random Forest a atteint un score ROC-AUC de 85%.",
            "technologies": ["Python", "Pandas", "Scikit-learn", "Matplotlib", "Seaborn", "Random Forest"],
            "github": "https://github.com/dze-shalom/Chunk-Analysis",
            "live": null
        },
        {
            "id": 5,
            "title": "Site Web MUFEPREC",
            "category": "web-development",
            "image": "assets/images/projects/web-development/mufeprec-website.jpeg",
            "description": "Plateforme scolaire full-stack construite avec frontend HTML, CSS et Javascript et backend Node.js. Les fonctionnalités incluent l'authentification des utilisateurs, le catalogue de produits, le panier d'achat et l'intégration de paiement.",
            "technologies": ["HTML", "CSS", "Javascript", "Node.js"],
            "github": "https://github.com/dze-shalom/MUFEPREC-WEBSITE",
            "live": "https://mufeprecweb.netlify.app/"
        },
        {
            "id": 6,
            "title": "Site Web Portfolio",
            "category": "web-development",
            "image": "assets/images/projects/web-development/portfolio-website.jpg",
            "description": "Site web portfolio moderne et réactif construit avec HTML5, CSS3 et JavaScript purs. Fonctionnalités : basculement de thème clair/sombre et animations fluides.",
            "technologies": ["HTML5", "CSS3", "JavaScript", "Particles.js", "Design Réactif"],
            "github": "https://github.com/dze-shalom/MyPortfolio",
            "live": "https://dzekumshalom.netlify.app/"
        },
        {
            "id": 7,
            "title": "AgriBot - Assistant IA Agricole",
            "category": "data-science",
            "image": "assets/images/projects/data-science/agribot.png",
            "description": "Chatbot alimenté par l'IA spécialisé dans l'agriculture, fournissant des réponses aux questions agricoles, l'analyse des maladies par reconnaissance d'image et des conseils de plantation basés sur la localisation. Aide les agriculteurs à prendre des décisions basées sur les données pour de meilleurs rendements.",
            "technologies": ["Python", "Machine Learning", "Flask", "HTML", "Tailwind CSS", "JavaScript", "NLP", "TensorFlow", "OpenCV", "API de Géolocalisation", "PostgreSQL"],
            "github": "https://github.com/dze-shalom/agribot",
            "live": "https://agribot-1-ed6c.onrender.com"
        }
    ]
};

// ===== TRANSLATIONS =====
const TRANSLATIONS = {
    en: {
        nav: {
            home: "Home",
            about: "About",
            education: "Education",
            projects: "Projects",
            contact: "Contact",
            resume: "Resume"
        },
        hero: {
            greeting: "Hello, my name is",
            subtitle: "Data Scientist",
            description: "I specialize in electrical and electronic engineering with expertise in telecommunications, network engineering, data science, full stack web development, and mobile app development. With multiple advanced degrees and a passion for innovation, I bring a unique blend of technical knowledge and analytical skills to solve complex problems across multiple domains.",
            viewProjects: "View Projects",
            downloadResume: "Download Resume",
            getInTouch: "Get In Touch"
        },
        about: {
            title: "About Me",
            leadText: "I am a passionate data scientist with a strong educational background in electrical and electronic engineering, telecommunications, network engineering, and data science. With a B.Eng, M.Tech, and M.Sc degree, I have cultivated a diverse skill set that allows me to approach problems from multiple angles.",
            paragraph1: "My journey began with electrical engineering, where I developed a strong foundation in circuit design, power systems, and electronics. I then specialized in telecommunications and network engineering, gaining expertise in communication protocols, network architecture, and system optimization.",
            paragraph2: "Most recently, I am completing my M.Sc in Data Science at AIMS, I've expanded my expertise to include machine learning, statistical analysis, and data visualization. Alongside my academic pursuits, I've developed strong skills in full stack web development and mobile app development, allowing me to create end-to-end solutions.",
            paragraph3: "This interdisciplinary background enables me to approach problems from multiple perspectives, whether it's developing IoT solutions, creating data-driven web applications, or building mobile apps that solve real-world problems.",
            skillsTitle: "Skills & Technologies"
        },
        education: {
            title: "Education"
        },
        projects: {
            title: "Featured Projects",
            filters: {
                all: "All",
                engineering: "Engineering",
                dataScience: "Data Science",
                webDevelopment: "Web Development",
                mobileApps: "Mobile Apps"
            }
        },
        contact: {
            title: "Get In Touch",
            intro: "I'm currently open to new opportunities and collaborations. Whether you have a question, a project idea, or just want to say hello, feel free to reach out!",
            email: "Email",
            linkedin: "LinkedIn",
            linkedinText: "Connect with me",
            location: "Location",
            locationText: "Molyko-Buea, Cameroon",
            namePlaceholder: "Your Name",
            emailPlaceholder: "Your Email",
            subjectPlaceholder: "Subject",
            messagePlaceholder: "Your Message",
            sendMessage: "Send Message"
        },
        footer: {
            rights: "All rights reserved."
        }
    },
    fr: {
        nav: {
            home: "Accueil",
            about: "À Propos",
            education: "Éducation",
            projects: "Projets",
            contact: "Contact",
            resume: "CV"
        },
        hero: {
            greeting: "Bonjour, je m'appelle",
            subtitle: "Data Scientist",
            description: "Je me spécialise dans l'ingénierie électrique et électronique avec une expertise en télécommunications, ingénierie réseau, science des données, développement web full stack et développement d'applications mobiles. Avec plusieurs diplômes avancés et une passion pour l'innovation, j'apporte une combinaison unique de connaissances techniques et de compétences analytiques pour résoudre des problèmes complexes dans plusieurs domaines.",
            viewProjects: "Voir les Projets",
            downloadResume: "Télécharger le CV",
            getInTouch: "Me Contacter"
        },
        about: {
            title: "À Propos de Moi",
            leadText: "Je suis un data scientist passionné avec une solide formation en ingénierie électrique et électronique, télécommunications, ingénierie réseau et science des données. Avec un B.Eng, M.Tech et M.Sc, j'ai cultivé un ensemble de compétences diversifié qui me permet d'aborder les problèmes sous plusieurs angles.",
            paragraph1: "Mon parcours a commencé avec l'ingénierie électrique, où j'ai développé une base solide en conception de circuits, systèmes d'alimentation et électronique. Je me suis ensuite spécialisé dans les télécommunications et l'ingénierie réseau, acquérant une expertise en protocoles de communication, architecture réseau et optimisation des systèmes.",
            paragraph2: "Plus récemment, en terminant ma M.Sc en Science des Données à AIMS, j'ai élargi mon expertise pour inclure l'apprentissage automatique, l'analyse statistique et la visualisation des données. Parallèlement à mes études académiques, j'ai développé de solides compétences en développement web full stack et développement d'applications mobiles, me permettant de créer des solutions de bout en bout.",
            paragraph3: "Cette formation interdisciplinaire me permet d'aborder les problèmes sous plusieurs perspectives, que ce soit pour développer des solutions IoT, créer des applications web basées sur les données ou créer des applications mobiles qui résolvent des problèmes du monde réel.",
            skillsTitle: "Compétences & Technologies"
        },
        education: {
            title: "Éducation"
        },
        projects: {
            title: "Projets Présentés",
            filters: {
                all: "Tous",
                engineering: "Ingénierie",
                dataScience: "Science des Données",
                webDevelopment: "Développement Web",
                mobileApps: "Applications Mobiles"
            }
        },
        contact: {
            title: "Contactez-moi",
            intro: "Je suis actuellement ouvert à de nouvelles opportunités et collaborations. Que vous ayez une question, une idée de projet, ou que vous souhaitiez simplement dire bonjour, n'hésitez pas à me contacter!",
            email: "Email",
            linkedin: "LinkedIn",
            linkedinText: "Connectez-vous avec moi",
            location: "Localisation",
            locationText: "Molyko-Buea, Cameroun",
            namePlaceholder: "Votre Nom",
            emailPlaceholder: "Votre Email",
            subjectPlaceholder: "Sujet",
            messagePlaceholder: "Votre Message",
            sendMessage: "Envoyer le Message"
        },
        footer: {
            rights: "Tous droits réservés."
        }
    }
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('Portfolio initializing...');
    
    // Initialize core functionality
    initializeParticles();
    initializeLanguageToggle();
    initializeThemeToggle();
    initializeMobileMenu();
    initializeScrollEffects();
    initializeSmoothScroll();
    initializeContactForm();
    initializeImageHandlers();
    initializeHeroAnimations();
    
    // Load data first
    setTimeout(() => {
        loadAllData().then(() => {
            console.log('Data loaded successfully');

            // Initialize filtering after data is loaded and rendered
            setTimeout(() => {
                initializeFiltering();
                initializeScrollAnimations();
                // Update language after everything is loaded
                updateLanguage(currentLang);
            }, 1000);

        }).catch((error) => {
            console.error('Failed to load data:', error);
        });
    }, 500);
    
    console.log('Portfolio initialization complete!');
});

// ===== HERO ANIMATIONS =====
function initializeHeroAnimations() {
    const heroElements = [
        '.hero-greeting',
        '.hero-title', 
        '.hero-subtitle',
        '.hero-description',
        '.hero-actions',
        '.hero-social'
    ];
    
    heroElements.forEach((selector, index) => {
        const element = document.querySelector(selector);
        if (element) {
            setTimeout(() => {
                element.classList.add('animate-fade-up');
            }, index * 200);
        }
    });
}

// ===== PARTICLES.JS =====
function initializeParticles() {
    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            particles: {
                number: { value: 80, density: { enable: true, value_area: 800 } },
                color: { value: "#64ffda" },
                shape: { type: "circle" },
                opacity: { value: 0.5, random: false },
                size: { value: 3, random: true },
                line_linked: { enable: true, distance: 150, color: "#64ffda", opacity: 0.4, width: 1 },
                move: { enable: true, speed: 6, direction: "none", out_mode: "out" }
            },
            interactivity: {
                detect_on: "canvas",
                events: { onhover: { enable: true, mode: "repulse" }, onclick: { enable: true, mode: "push" } },
                modes: { repulse: { distance: 200, duration: 0.4 }, push: { particles_nb: 4 } }
            },
            retina_detect: true
        });
    }
}

function updateParticlesTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    if (typeof pJSDom !== 'undefined' && pJSDom[0] && pJSDom[0].pJS) {
        const particleColor = currentTheme === 'dark' ? '#64ffda' : '#0891b2';
        if (pJSDom[0].pJS.particles) {
            pJSDom[0].pJS.particles.color.value = particleColor;
            pJSDom[0].pJS.particles.line_linked.color = particleColor;
        }
    }
}

// ===== THEME TOGGLE =====
function initializeThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    const themeIcon = themeToggle.querySelector('i');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
        
        setTimeout(() => updateParticlesTheme(), 300);
    });

    function updateThemeIcon(theme) {
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

// ===== LANGUAGE TOGGLE =====
function initializeLanguageToggle() {
    const langToggle = document.getElementById('lang-toggle');
    if (!langToggle) return;

    const langText = langToggle.querySelector('.lang-text');
    const savedLang = localStorage.getItem('language') || 'en';
    currentLang = savedLang;
    updateLanguage(currentLang);
    updateLangButton(currentLang);

    langToggle.addEventListener('click', () => {
        currentLang = currentLang === 'en' ? 'fr' : 'en';
        localStorage.setItem('language', currentLang);
        updateLanguage(currentLang);
        updateLangButton(currentLang);
    });

    function updateLangButton(lang) {
        if (langText) {
            langText.textContent = lang === 'en' ? 'FR' : 'EN';
        }
    }
}

function updateLanguage(lang) {
    const t = TRANSLATIONS[lang];

    // Update navigation
    const navLinks = document.querySelectorAll('.nav-link');
    if (navLinks[0]) navLinks[0].textContent = t.nav.home;
    if (navLinks[1]) navLinks[1].textContent = t.nav.about;
    if (navLinks[2]) navLinks[2].textContent = t.nav.education;
    if (navLinks[3]) navLinks[3].textContent = t.nav.projects;
    if (navLinks[4]) navLinks[4].textContent = t.nav.contact;

    const resumeText = document.querySelector('.resume-text');
    if (resumeText) resumeText.textContent = t.nav.resume;

    // Update hero section
    const heroGreeting = document.querySelector('.hero-greeting');
    const heroSubtitle = document.querySelector('.hero-subtitle');
    const heroDescription = document.querySelector('.hero-description');
    if (heroGreeting) heroGreeting.textContent = t.hero.greeting;
    if (heroSubtitle) heroSubtitle.textContent = t.hero.subtitle;
    if (heroDescription) heroDescription.textContent = t.hero.description;

    const ctaBtns = document.querySelectorAll('.cta-btn');
    if (ctaBtns[0]) ctaBtns[0].textContent = t.hero.viewProjects;
    if (ctaBtns[1]) ctaBtns[1].textContent = t.hero.downloadResume;
    if (ctaBtns[2]) ctaBtns[2].textContent = t.hero.getInTouch;

    // Update section titles
    const sectionTitles = document.querySelectorAll('.section-title');
    if (sectionTitles[0]) sectionTitles[0].textContent = t.about.title;
    if (sectionTitles[1]) sectionTitles[1].textContent = t.education.title;
    if (sectionTitles[2]) sectionTitles[2].textContent = t.projects.title;
    if (sectionTitles[3]) sectionTitles[3].textContent = t.contact.title;

    // Update About section content
    const leadText = document.querySelector('.lead-text');
    const aboutParagraphs = document.querySelectorAll('.about-text p');
    const aboutSkillsTitle = document.querySelector('.about-text h3');

    if (leadText) leadText.textContent = t.about.leadText;
    if (aboutParagraphs[1]) aboutParagraphs[1].textContent = t.about.paragraph1;
    if (aboutParagraphs[2]) aboutParagraphs[2].textContent = t.about.paragraph2;
    if (aboutParagraphs[3]) aboutParagraphs[3].textContent = t.about.paragraph3;
    if (aboutSkillsTitle) aboutSkillsTitle.textContent = t.about.skillsTitle;

    // Update project filters
    const filterBtns = document.querySelectorAll('.filter-btn');
    if (filterBtns[0]) filterBtns[0].textContent = t.projects.filters.all;
    if (filterBtns[1]) filterBtns[1].textContent = t.projects.filters.engineering;
    if (filterBtns[2]) filterBtns[2].textContent = t.projects.filters.dataScience;
    if (filterBtns[3]) filterBtns[3].textContent = t.projects.filters.webDevelopment;
    if (filterBtns[4]) filterBtns[4].textContent = t.projects.filters.mobileApps;

    // Update contact section
    const contactIntro = document.querySelector('.contact-intro p');
    if (contactIntro) contactIntro.textContent = t.contact.intro;

    const contactDetails = document.querySelectorAll('.contact-details h3');
    if (contactDetails[0]) contactDetails[0].textContent = t.contact.email;
    if (contactDetails[1]) contactDetails[1].textContent = t.contact.linkedin;
    if (contactDetails[2]) contactDetails[2].textContent = t.contact.location;

    const contactLinks = document.querySelectorAll('.contact-details a.contact-link');
    if (contactLinks[1]) contactLinks[1].textContent = t.contact.linkedinText;

    const contactLocation = document.querySelectorAll('.contact-details p');
    if (contactLocation[2]) contactLocation[2].textContent = t.contact.locationText;

    // Update form placeholders
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const subjectInput = document.getElementById('subject');
    const messageInput = document.getElementById('message');
    const submitBtn = document.querySelector('.submit-btn .btn-text');

    if (nameInput) nameInput.placeholder = t.contact.namePlaceholder;
    if (emailInput) emailInput.placeholder = t.contact.emailPlaceholder;
    if (subjectInput) subjectInput.placeholder = t.contact.subjectPlaceholder;
    if (messageInput) messageInput.placeholder = t.contact.messagePlaceholder;
    if (submitBtn) submitBtn.textContent = t.contact.sendMessage;

    // Update footer
    const footerText = document.querySelector('.footer-content p');
    if (footerText) {
        footerText.textContent = `© ${new Date().getFullYear()} Dze-Kum Shalom Chow. ${t.footer.rights}`;
    }

    // Re-render projects with translated data
    const projectData = lang === 'fr' ? PORTFOLIO_DATA_FR.projects : PORTFOLIO_DATA.projects;
    renderProjects(projectData);

    // Re-render education with translated data
    const educationData = lang === 'fr' ? PORTFOLIO_DATA_FR.education : PORTFOLIO_DATA.education;
    renderEducationTimeline(educationData);
}

// ===== MOBILE MENU =====
function initializeMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navLinks = document.getElementById('nav-links');
    const navLinksItems = document.querySelectorAll('.nav-link');

    if (!mobileMenuBtn || !navLinks) return;

    const toggleMenu = (e) => {
        e.preventDefault();
        e.stopPropagation();
        navLinks.classList.toggle('active');
        mobileMenuBtn.classList.toggle('active');
        document.body.style.overflow = navLinks.classList.contains('active') ? 'hidden' : 'auto';
    };

    // Add both click and touchstart for better mobile support
    mobileMenuBtn.addEventListener('click', toggleMenu);
    mobileMenuBtn.addEventListener('touchstart', toggleMenu, { passive: false });

    const closeMenu = () => {
        navLinks.classList.remove('active');
        mobileMenuBtn.classList.remove('active');
        document.body.style.overflow = 'auto';
    };

    navLinksItems.forEach(link => {
        link.addEventListener('click', closeMenu);
        link.addEventListener('touchstart', closeMenu);
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (navLinks.classList.contains('active') &&
            !navLinks.contains(e.target) &&
            !mobileMenuBtn.contains(e.target)) {
            closeMenu();
        }
    });
}

// ===== SCROLL EFFECTS =====
function initializeScrollEffects() {
    const header = document.getElementById('header');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            header?.classList.add('scrolled');
        } else {
            header?.classList.remove('scrolled');
        }
        updateActiveNavLink();
    });
}

function updateActiveNavLink() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let currentSection = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 150;
        const sectionHeight = section.offsetHeight;
        
        if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
            currentSection = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentSection}`) {
            link.classList.add('active');
        }
    });
}

// ===== SCROLL ANIMATIONS =====
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                if (entry.target.classList.contains('skill-category')) {
                    animateSkillBars(entry.target);
                }
                
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const elementsToAnimate = document.querySelectorAll(`
        .education-item,
        .skill-category,
        .project-card,
        .blog-card,
        .animate-on-scroll
    `);
    
    elementsToAnimate.forEach(el => observer.observe(el));
}

function animateSkillBars(skillCategory) {
    const skillBars = skillCategory.querySelectorAll('.skill-progress');
    
    skillBars.forEach((bar, index) => {
        setTimeout(() => {
            const targetWidth = bar.style.width || bar.getAttribute('data-width');
            if (targetWidth) {
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = targetWidth;
                }, 100);
            }
        }, index * 100);
    });
}

// ===== SMOOTH SCROLL =====
function initializeSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            
            if (target) {
                const targetPosition = target.offsetTop - 80;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ===== DATA LOADING =====
async function loadAllData() {
    console.log('Loading portfolio data...');
    
    try {
        renderEducationTimeline(PORTFOLIO_DATA.education);
        renderSkills(PORTFOLIO_DATA.skillCategories);
        
        projectsData = PORTFOLIO_DATA.projects;
        blogData = PORTFOLIO_DATA.blog;
        
        renderProjects(projectsData);
        renderBlogPosts(blogData);
        
        console.log('All data loaded successfully');
        return true;
        
    } catch (error) {
        console.error('Error loading data:', error);
        return false;
    }
}

// ===== RENDER FUNCTIONS =====
function renderEducationTimeline(education) {
    const timeline = document.getElementById('education-timeline');
    if (!timeline) return;
    
    timeline.innerHTML = education.map(item => `
        <div class="education-item">
            <div class="education-content">
                <div class="education-year">${item.year}</div>
                <h3 class="education-degree">${item.degree}</h3>
                <h4 class="education-institution">${item.institution}</h4>
                <p class="education-description">${item.description}</p>
                ${item.achievements ? `
                    <ul class="education-achievements">
                        ${item.achievements.map(achievement => `<li>${achievement}</li>`).join('')}
                    </ul>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function renderSkills(categories) {
    const skillsContainer = document.getElementById('skills-categories');
    if (!skillsContainer) return;
    
    skillsContainer.innerHTML = categories.map(category => `
        <div class="skill-category">
            <h3 class="category-title">
                <i class="${category.icon}"></i>
                ${category.name}
            </h3>
            <div class="skills-list">
                ${category.skills.map(skill => `
                    <div class="skill-item">
                        <div class="skill-info">
                            <span class="skill-name">${skill.name}</span>
                            <span class="skill-level">${skill.level}%</span>
                        </div>
                        <div class="skill-bar">
                            <div class="skill-progress" data-width="${skill.level}%" style="width: ${skill.level}%"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function renderProjects(projects) {
    const projectsGrid = document.getElementById('projects-grid');
    if (!projectsGrid) return;
    
    projectsGrid.innerHTML = projects.map(project => `
        <div class="project-card" data-category="${project.category}">
            <div class="project-image">
                <img src="${project.image}"
                     alt="${project.title}"
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjI1MCIgdmlld0JveD0iMCAwIDQwMCAyNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMjUwIiBmaWxsPSIjMTEyMjQwIi8+CjxyZWN0IHg9IjE1MCIgeT0iMTAwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjUwIiBmaWxsPSIjNjRmZmRhIiBvcGFjaXR5PSIwLjMiLz4KPHN2ZyB4PSIxNzAiIHk9IjExNSIgd2lkdGg9IjYwIiBoZWlnaHQ9IjIwIiBmaWxsPSIjNjRmZmRhIj4KPAD8dGV4dCB4PSIwIiB5PSIxNSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOGI5MmIwIj5Qcm9qZWN0PC90ZXh0Pgo8L3N2Zz4KPC9zdmc+'">
                <div class="project-buttons">
                    ${project.github ? `<a href="${project.github}" target="_blank" rel="noopener noreferrer" class="project-btn github-btn" title="View Code">
                        <i class="fab fa-github"></i>
                    </a>` : ''}
                    ${project.live ? `<a href="${project.live}" target="_blank" rel="noopener noreferrer" class="project-btn live-btn" title="Live Demo">
                        <i class="fas fa-external-link-alt"></i>
                    </a>` : ''}
                </div>
            </div>
            <div class="project-content">
                <h3 class="project-title">${project.title}</h3>
                <p class="project-description">${project.description}</p>
                <div class="project-tags">
                    ${project.technologies.map(tech => `<span class="project-tag">${tech}</span>`).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

function renderBlogPosts(posts) {
    const blogGrid = document.getElementById('blog-grid');
    if (!blogGrid) return;
    
    blogGrid.innerHTML = posts.map(post => `
        <article class="blog-card" data-category="${post.category}">
            <div class="blog-image">
                <img src="${post.image}" 
                     alt="${post.title}"
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDQwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMTEyMjQwIi8+CjxyZWN0IHg9IjUwIiB5PSI2MCIgd2lkdGg9IjMwMCIgaGVpZ2h0PSI4MCIgZmlsbD0iIzY0ZmZkYSIgb3BhY2l0eT0iMC4zIi8+CjxzdmcgeD0iMTAwIiB5PSI5MCIgd2lkdGg9IjIwMCIgaGVpZ2h0PSIyMCIgZmlsbD0iIzY0ZmZkYSI+CiAgPHRleHQgeD0iNzAiIHk9IjE1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM4YjkyYjAiPkJsb2cgUG9zdDwvdGV4dD4KPC9zdmc+Cjwvc3ZnPg=='">
            </div>
            <div class="blog-content">
                <div class="blog-meta">
                    <span class="blog-date">${post.date}</span>
                    <span class="blog-category">${post.category}</span>
                </div>
                <h3 class="blog-title">${post.title}</h3>
                <p class="blog-excerpt">${post.excerpt}</p>
                <a href="${post.link}" class="read-more">Read More <i class="fas fa-arrow-right"></i></a>
            </div>
        </article>
    `).join('');
}

// ===== FIXED FILTERING SYSTEM =====
function initializeFiltering() {
    console.log('Initializing filtering system...');
    setupProjectFiltering();
}

function setupProjectFiltering() {
    console.log('Setting up project filtering...');

    // Target the correct selectors based on your HTML
    const filterButtons = document.querySelectorAll('.project-filters .filter-btn');

    console.log('Found project filter buttons:', filterButtons.length);

    if (filterButtons.length === 0) {
        console.warn('No filter buttons found! Check your HTML structure.');
        return;
    }

    // Add event listeners to filter buttons
    filterButtons.forEach((button) => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const filter = this.getAttribute('data-filter');
            console.log('Filter clicked:', filter);

            // Update active button state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Get project cards dynamically each time (in case they were re-rendered)
            const projectCards = document.querySelectorAll('.project-card');
            console.log('Found project cards:', projectCards.length);

            // Filter project cards with animation
            projectCards.forEach(card => {
                const category = card.getAttribute('data-category');
                console.log('Card category:', category, 'Filter:', filter);

                if (filter === 'all' || category === filter) {
                    // Show the card
                    card.style.display = 'block';
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.8)';

                    // Animate in
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'scale(1)';
                        card.style.transition = 'all 0.3s ease';
                    }, 50);
                } else {
                    // Hide the card
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.8)';
                    card.style.transition = 'all 0.3s ease';

                    setTimeout(() => {
                        card.style.display = 'none';
                    }, 300);
                }
            });
        });
    });

    console.log('Project filtering initialized successfully!');
}

// ===== CONTACT FORM =====
function initializeContactForm() {
    const form = document.getElementById('contact-form');
    if (!form) return;
    
    const submitBtn = form.querySelector('.submit-btn');
    const btnText = submitBtn?.querySelector('.btn-text');
    const btnLoading = submitBtn?.querySelector('.btn-loading');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (submitBtn) {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            if (btnText) btnText.style.display = 'none';
            if (btnLoading) btnLoading.style.display = 'block';
        }

        const formData = new FormData(form);
        const data = {
            name: formData.get('name'),
            email: formData.get('email'),
            subject: formData.get('subject'),
            message: formData.get('message')
        };

        try {
            const response = await fetch('/send-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showNotification('Message sent successfully! I\'ll get back to you soon.', 'success');
                form.reset();
            } else {
                throw new Error('Server error');
            }
        } catch (error) {
            const mailtoLink = `mailto:dzekumshalomchow@gmail.com?subject=${encodeURIComponent(data.subject)}&body=${encodeURIComponent(`Name: ${data.name}\nEmail: ${data.email}\n\nMessage:\n${data.message}`)}`;
            window.location.href = mailtoLink;
            showNotification('Opening your email client...', 'success');
        } finally {
            if (submitBtn) {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
                if (btnText) btnText.style.display = 'block';
                if (btnLoading) btnLoading.style.display = 'none';
            }
        }
    });
}

// ===== NOTIFICATION SYSTEM =====
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    
    const messageElement = notification.querySelector('.notification-message');
    const closeBtn = notification.querySelector('.notification-close');
    
    if (messageElement) messageElement.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    const autoHideTimeout = setTimeout(() => {
        hideNotification();
    }, 5000);
    
    if (closeBtn) {
        closeBtn.onclick = () => {
            clearTimeout(autoHideTimeout);
            hideNotification();
        };
    }
    
    function hideNotification() {
        notification.classList.remove('show');
    }
}

// ===== IMAGE HANDLERS =====
function initializeImageHandlers() {
    document.addEventListener('error', (e) => {
        if (e.target.tagName === 'IMG') {
            e.target.classList.add('error');
            
            if (!e.target.src.includes('data:image/svg+xml')) {
                if (e.target.closest('.project-card')) {
                    e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjI1MCIgdmlld0JveD0iMCAwIDQwMCAyNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMjUwIiBmaWxsPSIjMTEyMjQwIi8+CjxyZWN0IHg9IjE1MCIgeT0iMTAwIiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjUwIiBmaWxsPSIjNjRmZmRhIiBvcGFjaXR5PSIwLjMiLz4KPHN2ZyB4PSIxNzAiIHk9IjExNSIgd2lkdGg9IjYwIiBoZWlnaHQ9IjIwIiBmaWxsPSIjNjRmZmRhIj4KICA8dGV4dCB4PSIwIiB5PSIxNSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOGI5MmIwIj5Qcm9qZWN0PC90ZXh0Pgo8L3N2Zz4KPC9zdmc+';
                } else if (e.target.closest('.blog-card')) {
                    e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDQwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMTEyMjQwIi8+CjxyZWN0IHg9IjUwIiB5PSI2MCIgd2lkdGg9IjMwMCIgaGVpZ2h0PSI4MCIgZmlsbD0iIzY0ZmZkYSIgb3BhY2l0eT0iMC4zIi8+CjxzdmcgeD0iMTAwIiB5PSI5MCIgd2lkdGg9IjIwMCIgaGVpZ2h0PSIyMCIgZmlsbD0iIzY0ZmZkYSI+CiAgPHRleHQgeD0iNzAiIHk9IjE1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM4YjkyYjAiPkJsb2cgUG9zdDwvdGV4dD4KPC9zdmc+Cjwvc3ZnPg==';
                } else {
                    e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDMwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjMTEyMjQwIi8+CjxjaXJjbGUgY3g9IjE1MCIgY3k9IjEyMCIgcj0iNDAiIGZpbGw9IiM2NGZmZGEiLz4KPHBhdGggZD0iTTEwMCAyNDBIMjAwQzIwMCAyMTAgMTgwIDE5MCAxNTAgMTkwUzEwMCAyMTAgMTAwIDI0MFoiIGZpbGw9IiM2NGZmZGEiLz4KPHR4dCB4PSIxNTAiIHk9IjI3MCIgZmlsbD0iIzhiOTJiMCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5Qcm9maWxlIFBob3RvPC90eHQ+Cjwvc3ZnPgo=';
                }
            }
        }
    }, true);
}

// ===== ACCESSIBILITY =====
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const navLinks = document.getElementById('nav-links');
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        
        if (navLinks?.classList.contains('active')) {
            navLinks.classList.remove('active');
            mobileMenuBtn?.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    }
});

// ===== DEBUG AND TEST FUNCTIONS =====
window.debugProjectFiltering = function() {
    console.log('=== PROJECT FILTERING DEBUG ===');
    
    const filterButtons = document.querySelectorAll('.project-filters .filter-btn');
    const projectCards = document.querySelectorAll('.project-card');
    
    console.log('Filter buttons found:', filterButtons.length);
    console.log('Project cards found:', projectCards.length);
    
    console.log('Filter button data:');
    filterButtons.forEach((btn, i) => {
        console.log(`  Button ${i}: "${btn.textContent.trim()}" -> data-filter="${btn.getAttribute('data-filter')}"`);
    });
    
    console.log('Project card data:');
    projectCards.forEach((card, i) => {
        const title = card.querySelector('.project-title')?.textContent || 'No title';
        const category = card.getAttribute('data-category');
        console.log(`  Card ${i}: "${title}" -> data-category="${category}"`);
    });
    
    // Check if projects data matches categories
    if (typeof PORTFOLIO_DATA !== 'undefined' && PORTFOLIO_DATA.projects) {
        console.log('Available project categories in data:');
        const categories = [...new Set(PORTFOLIO_DATA.projects.map(p => p.category))];
        console.log(categories);
    }
};

window.testFilter = function(category = 'data-science') {
    console.log(`Testing filter: ${category}`);
    
    const cards = document.querySelectorAll('.project-card');
    
    cards.forEach(card => {
        const cardCategory = card.getAttribute('data-category');
        if (category === 'all' || cardCategory === category) {
            card.style.display = 'block';
            card.style.opacity = '1';
            card.style.transform = 'scale(1)';
            console.log(`Showing: ${cardCategory}`);
        } else {
            card.style.display = 'none';
            console.log(`Hiding: ${cardCategory}`);
        }
    });
};

window.forceReInitializeFiltering = function() {
    console.log('Force re-initializing filtering...');
    setTimeout(setupProjectFiltering, 100);
};

console.log('Portfolio loaded successfully!');
