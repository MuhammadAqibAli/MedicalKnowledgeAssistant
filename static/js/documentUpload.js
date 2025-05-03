document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const submitBtn = document.getElementById('submitBtn');
    const uploadForm = document.getElementById('uploadForm');
    
    if (!fileInput || !submitBtn || !uploadForm) return;
    
    // Update form UI when file is selected
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        
        if (file) {
            // Check file type
            const fileType = file.name.split('.').pop().toLowerCase();
            if (fileType !== 'pdf' && fileType !== 'docx') {
                alert('Please select a PDF or DOCX file.');
                this.value = '';
                return;
            }
            
            // Check file size (max 16MB)
            const maxSize = 16 * 1024 * 1024; // 16MB in bytes
            if (file.size > maxSize) {
                alert('File size exceeds the 16MB limit.');
                this.value = '';
                return;
            }
            
            // Set default title if empty based on filename
            const titleInput = document.getElementById('title');
            if (titleInput.value === '') {
                // Remove file extension and use as title
                const fileName = file.name.replace(/\.[^/.]+$/, "");
                
                // Convert to title case and clean up
                const titleCase = fileName
                    .replace(/[-_]/g, ' ')  // Replace dashes and underscores with spaces
                    .replace(/\b\w/g, l => l.toUpperCase()); // Title case
                
                titleInput.value = titleCase;
            }
            
            // Update button text
            submitBtn.innerHTML = `<i class="fas fa-upload"></i> Upload ${file.name}`;
        } else {
            // Reset button text if no file selected
            submitBtn.innerHTML = `<i class="fas fa-upload"></i> Upload and Process Document`;
        }
    });
    
    // Add form submission handler with validation
    uploadForm.addEventListener('submit', function(e) {
        const file = fileInput.files[0];
        const title = document.getElementById('title').value;
        const docType = document.getElementById('doc_type').value;
        
        if (!file) {
            e.preventDefault();
            alert('Please select a file to upload.');
            return;
        }
        
        if (!title.trim()) {
            e.preventDefault();
            alert('Please enter a document title.');
            return;
        }
        
        if (!docType) {
            e.preventDefault();
            alert('Please select a document type.');
            return;
        }
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing Document...';
        
        // Form will submit normally if all validations pass
    });
});
