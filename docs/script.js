document.addEventListener('DOMContentLoaded', () => {
    // ==========================================================================
    // Theme Toggle Logic
    // ==========================================================================
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const body = document.body;

    // Load theme preference from localStorage or default to dark-theme
    const savedTheme = localStorage.getItem('theme') || 'dark-theme';
    body.className = savedTheme;

    themeToggleBtn.addEventListener('click', () => {
        if (body.classList.contains('dark-theme')) {
            body.classList.replace('dark-theme', 'light-theme');
            localStorage.setItem('theme', 'light-theme');
        } else {
            body.classList.replace('light-theme', 'dark-theme');
            localStorage.setItem('theme', 'dark-theme');
        }
    });

    // ==========================================================================
    // Mobile Navigation Menu Logic
    // ==========================================================================
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const navMenu = document.getElementById('nav-menu');

    mobileMenuBtn.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        mobileMenuBtn.classList.toggle('active');
        
        // Toggle hamburger animation state
        const bars = mobileMenuBtn.querySelectorAll('.bar');
        if (mobileMenuBtn.classList.contains('active')) {
            bars[0].style.transform = 'rotate(-45deg) translate(-5px, 6px)';
            bars[1].style.opacity = '0';
            bars[2].style.transform = 'rotate(45deg) translate(-5px, -6px)';
        } else {
            bars[0].style.transform = 'none';
            bars[1].style.opacity = '1';
            bars[2].style.transform = 'none';
        }
    });

    // Close menu when clicking nav links on mobile
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                mobileMenuBtn.classList.remove('active');
                const bars = mobileMenuBtn.querySelectorAll('.bar');
                bars[0].style.transform = 'none';
                bars[1].style.opacity = '1';
                bars[2].style.transform = 'none';
            }
        });
    });

    // ==========================================================================
    // Quick Start Tabs Logic
    // ==========================================================================
    const tabDebBtn = document.getElementById('tab-btn-deb');
    const tabSrcBtn = document.getElementById('tab-btn-source');
    const contentDeb = document.getElementById('tab-content-deb');
    const contentSrc = document.getElementById('tab-content-source');

    if (tabDebBtn && tabSrcBtn) {
        tabDebBtn.addEventListener('click', () => {
            tabDebBtn.classList.add('active');
            tabSrcBtn.classList.remove('active');
            contentDeb.classList.add('active');
            contentSrc.classList.remove('active');
        });

        tabSrcBtn.addEventListener('click', () => {
            tabSrcBtn.classList.add('active');
            tabDebBtn.classList.remove('active');
            contentSrc.classList.add('active');
            contentDeb.classList.remove('active');
        });
    }

    // ==========================================================================
    // Clipboard Copy Logic
    // ==========================================================================
    const copyBtns = document.querySelectorAll('.copy-btn');
    
    copyBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const targetId = btn.getAttribute('data-target');
            const targetEl = document.getElementById(targetId);
            
            if (targetEl) {
                const textToCopy = targetEl.innerText;
                try {
                    await navigator.clipboard.writeText(textToCopy);
                    
                    // Visual feedback
                    btn.innerText = 'Copied!';
                    btn.classList.add('copied');
                    
                    setTimeout(() => {
                        btn.innerText = 'Copy';
                        btn.classList.remove('copied');
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy text: ', err);
                }
            }
        });
    });

    // ==========================================================================
    // Interactive Documentation Hub Logic
    // ==========================================================================
    const docNavBtns = document.querySelectorAll('.docs-nav-btn');
    const docPanels = document.querySelectorAll('.doc-panel');
    const docContent = document.querySelector('.docs-content');

    docNavBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const docId = btn.getAttribute('data-doc');
            const targetPanel = document.getElementById(`panel-${docId}`);

            if (targetPanel) {
                // Deactivate all nav buttons and panels
                docNavBtns.forEach(b => {
                    b.classList.remove('active');
                    b.setAttribute('aria-selected', 'false');
                });
                docPanels.forEach(p => p.classList.remove('active'));

                // Activate selected nav button and panel
                btn.classList.add('active');
                btn.setAttribute('aria-selected', 'true');
                targetPanel.classList.add('active');

                // Smooth scroll to top of documentation panel (useful for mobile layout)
                if (window.innerWidth <= 1024) {
                    docContent.scrollIntoView({ behavior: 'smooth' });
                } else {
                    const headerOffset = 100;
                    const elementPosition = docContent.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                    
                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
});
