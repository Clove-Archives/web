// Get all buttons and sections
const buttons = document.querySelectorAll('.sos-button');
const sections = document.querySelectorAll('.info-section');

// Add click event to each button
buttons.forEach(button => {
    button.addEventListener('click', () => {
        const sectionId = button.getAttribute('data-section');
        const targetSection = document.getElementById(sectionId);
        
        // Toggle the clicked section
        if (targetSection.classList.contains('hidden')) {
            // Hide all sections first
            sections.forEach(section => {
                section.classList.add('hidden');
            });
            
            // Show the target section
            targetSection.classList.remove('hidden');
            
            // Scroll to the section smoothly
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            // If already visible, hide it
            targetSection.classList.add('hidden');
        }
    });
});