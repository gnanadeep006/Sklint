/* SklinT Static Site - JavaScript */
/* Handles scroll animations, navigation, modals, and form interactions */

document.addEventListener('DOMContentLoaded', () => {
  // ========== Intersection Observer for Scroll Animations ==========
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '-50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    observer.observe(el);
  });

  // ========== Navigation Scroll Effect ==========
  const header = document.querySelector('.nav-header');
  if (header) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    });
  }

  // ========== Mobile Menu ==========
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const mobileMenu = document.querySelector('.mobile-menu');
  const mobileMenuClose = document.querySelector('.mobile-menu-close');

  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => {
      const isOpen = mobileMenu.classList.contains('open');
      if (isOpen) {
        mobileMenu.classList.remove('open');
        mobileMenuBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>`;
      } else {
        mobileMenu.classList.add('open');
        mobileMenuBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`;
      }
    });
  }

  // ========== Project Filtering (Projects Page) ==========
  const filterBtns = document.querySelectorAll('.filter-btn');
  const projectItems = document.querySelectorAll('.project-item');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const category = btn.dataset.category;

      // Update active state
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Filter projects
      projectItems.forEach(item => {
        if (category === 'All' || item.dataset.category === category) {
          item.style.display = '';
          item.style.animation = 'fadeInUp 0.4s ease forwards';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });

  // ========== Project Modal ==========
  const modalOverlay = document.querySelector('.project-modal-overlay');
  const modal = document.querySelector('.project-modal');
  const modalClose = document.querySelector('.modal-close');

  // Project data
  const projectData = {
    'living-structures': {
      title: 'Living Structures',
      category: 'Website',
      image: 'Screenshot 2026-02-01 134438.png',
      overview: 'Designed and developed a modern real estate website for Living Structures to professionally showcase their projects and brand. The site serves as a digital touchpoint for potential buyers and investors.',
      problem: 'The client lacked a structured online platform to present projects and capture customer inquiries effectively. This limited their reach and reduced lead conversion opportunities.',
      solution: 'Created a responsive, user-friendly website with clear project showcases and lead-generation contact forms. The design focused on clarity, trust, and easy navigation across devices.',
      outcome: 'Enhanced online presence, improved project visibility, and consistent client inquiries through the website. The website now acts as a key marketing and lead-generation tool for the business.',
      link: 'https://living.pythonanywhere.com/'
    },
    'pulse-studio': {
      title: 'Pulse Studio',
      category: 'Brand Identity',
      image: 'https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=800&h=600&fit=crop',
      overview: 'Pulse Studio is a boutique music production house serving independent artists. They needed a brand that felt premium yet approachable.',
      problem: 'Existing music studio brands either felt overly corporate or too casual. Pulse wanted to attract serious artists without appearing intimidating.',
      solution: 'We developed a visual identity built on rhythm and movement — dynamic typography, a warm color palette, and patterns inspired by sound waves.',
      outcome: 'The rebrand helped Pulse secure partnerships with three major record labels and doubled their inquiry rate within six months.'
    },
    'aura-finance': {
      title: 'Aura Finance',
      category: 'Web App',
      image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=600&fit=crop',
      overview: 'Aura Finance needed a dashboard that made complex financial data feel accessible and empowering for everyday users.',
      problem: 'Most finance apps overwhelm users with data, creating anxiety rather than clarity. Aura wanted to change how people feel about checking their finances.',
      solution: 'We designed a calm, spacious interface with progressive disclosure — showing key insights first and details on demand. Custom data visualizations tell stories, not just numbers.',
      outcome: 'User satisfaction scores reached 4.8/5, with 89% of users reporting they feel more confident about their financial decisions.'
    },
    'nomad-journal': {
      title: 'Nomad Journal',
      category: 'App Design',
      image: 'https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=800&h=600&fit=crop',
      overview: 'Nomad Journal is for travelers who want to document experiences, not just destinations. The app combines journaling with subtle location tracking.',
      problem: 'Travel apps focus on logistics — bookings, maps, itineraries. There was no thoughtful space for reflection and memory-making.',
      solution: 'We created a beautiful writing interface with optional photo integration, auto-generated location stamps, and a private sharing feature for sending moments to loved ones.',
      outcome: "Featured in the App Store's 'Apps We Love' and achieved 50,000 downloads in the first month."
    },
    'verdant-living': {
      title: 'Verdant Living',
      category: 'Website',
      image: 'https://images.unsplash.com/photo-1618220179428-22790b461013?w=800&h=600&fit=crop',
      overview: 'Verdant Living sells thoughtfully sourced home products with a focus on sustainability. Their old website didn\'t reflect their values.',
      problem: 'The previous site prioritized conversion over experience. It felt generic and failed to communicate the care behind each product.',
      solution: 'We built a slower, more intentional shopping experience — rich product stories, transparency about sourcing, and photography that shows products in real homes.',
      outcome: 'Average order value increased by 40%, and customer reviews frequently mention the website experience as a deciding factor.'
    },
    'cipher-security': {
      title: 'Cipher Security',
      category: 'Brand & Web',
      image: 'https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&h=600&fit=crop',
      overview: 'Cipher needed to stand out in the crowded cybersecurity space without resorting to clichéd dark themes and matrix-style graphics.',
      problem: 'Cybersecurity brands often feel either intimidating or overly technical. Cipher wanted to communicate trust and expertise without alienating non-technical decision-makers.',
      solution: 'We crafted a clean, confident brand with unexpected warmth. Clear language replaced jargon, and the visual system used light, open compositions.',
      outcome: 'Lead generation improved by 200%, with sales cycles shortening due to better-qualified prospects who understood the value proposition immediately.'
    }
  };
  const projectDataEl = document.getElementById('project-data');
  if (projectDataEl) {
    Object.assign(projectData, JSON.parse(projectDataEl.textContent));
  }

  document.querySelectorAll('.project-card').forEach(card => {
    const fallbackLink = card.querySelector('.arrow-btn[href]');

    // Make non-anchor cards keyboard-accessible when they behave like links.
    if (!card.dataset.project && fallbackLink) {
      card.tabIndex = 0;
      card.setAttribute('role', 'link');
    }

    card.addEventListener('click', () => {
      const projectId = card.dataset.project;
      const data = projectData[projectId];

      if (data && modalOverlay) {
        // Populate modal
        const cardImageSrc = card.querySelector('.project-card-image img')?.getAttribute('src');
        document.querySelector('.modal-image img').src = cardImageSrc || data.image;
        document.querySelector('.modal-image img').alt = data.title;
        document.querySelector('.modal-body .category-badge').textContent = data.category;
        document.querySelector('.modal-body .modal-title').textContent = data.title;
        document.querySelector('.detail-overview').textContent = data.overview;
        document.querySelector('.detail-problem').textContent = data.problem;
        document.querySelector('.detail-solution').textContent = data.solution;
        document.querySelector('.detail-outcome').textContent = data.outcome;

        const visitLink = document.querySelector('.modal-visit-link');
        if (data.link) {
          visitLink.href = data.link;
          visitLink.style.display = 'inline-flex';
        } else {
          visitLink.style.display = 'none';
        }

        modalOverlay.classList.add('open');
        document.body.style.overflow = 'hidden';
        return;
      }

      if (fallbackLink) {
        window.location.href = fallbackLink.href;
      }
    });

    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        card.click();
      }
    });
  });

  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay || e.target.classList.contains('project-modal-bg')) {
        closeModal();
      }
    });
  }

  if (modalClose) {
    modalClose.addEventListener('click', closeModal);
  }

  function closeModal() {
    if (modalOverlay) {
      modalOverlay.classList.remove('open');
      document.body.style.overflow = '';
    }
  }

  // Close modal on escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  // ========== Contact Form ==========
  const contactForm = document.querySelector('.contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', () => {
      const submitBtn = contactForm.querySelector('.submit-btn');
      const btnText = submitBtn.querySelector('.btn-text');
      const btnSpinner = submitBtn.querySelector('.btn-spinner');

      // Show loading
      if (btnText) btnText.style.display = 'none';
      if (btnSpinner) btnSpinner.style.display = 'flex';
      submitBtn.disabled = true;
      submitBtn.style.opacity = '0.5';
    });
  }

  // ========== Toast ==========
  function showToast(title, message) {
    const toast = document.querySelector('.toast');
    if (!toast) return;

    toast.querySelector('h4').textContent = title;
    toast.querySelector('p').textContent = message;
    toast.classList.add('show');

    setTimeout(() => {
      toast.classList.remove('show');
    }, 3000);
  }

  // ========== 3D Parallax Card (About page) ==========
  const aboutCard = document.querySelector('.about-card');
  if (aboutCard) {
    aboutCard.addEventListener('mousemove', (e) => {
      const rect = aboutCard.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const mouseX = (e.clientX - centerX) / rect.width;
      const mouseY = (e.clientY - centerY) / rect.height;

      const rotateX = mouseY * -3;
      const rotateY = mouseX * 3;

      aboutCard.style.transform = `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    });

    aboutCard.addEventListener('mouseleave', () => {
      aboutCard.style.transform = 'perspective(1200px) rotateX(0deg) rotateY(0deg)';
      aboutCard.style.transition = 'transform 0.5s ease';
      setTimeout(() => { aboutCard.style.transition = ''; }, 500);
    });
  }

  // ========== Active Nav Link ==========
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link, .mobile-menu a').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage || (currentPage === 'index.html' && href === 'index.html')) {
      link.classList.add('active');
    }
  });
});

