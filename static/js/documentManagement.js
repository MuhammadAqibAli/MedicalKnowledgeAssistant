document.addEventListener('DOMContentLoaded', function() {
    const documentsTable = document.getElementById('documentsTable');
    const documentSearchInput = document.getElementById('documentSearchInput');
    const documentSearchBtn = document.getElementById('documentSearchBtn');
    const generatedContentList = document.getElementById('generatedContentList');
    
    // Load generated content
    loadGeneratedContent();
    
    // Handle document search
    if (documentSearchInput && documentSearchBtn) {
        documentSearchBtn.addEventListener('click', function() {
            searchDocuments(documentSearchInput.value);
        });
        
        documentSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchDocuments(documentSearchInput.value);
            }
        });
    }
    
    // Handle view document buttons
    const viewDocButtons = document.querySelectorAll('.view-doc-btn');
    if (viewDocButtons.length > 0) {
        viewDocButtons.forEach(button => {
            button.addEventListener('click', function() {
                const docId = this.getAttribute('data-doc-id');
                viewDocument(docId);
            });
        });
    }
    
    // Handle generate from document buttons
    const generateFromDocButtons = document.querySelectorAll('.generate-from-doc-btn');
    if (generateFromDocButtons.length > 0) {
        generateFromDocButtons.forEach(button => {
            button.addEventListener('click', function() {
                const docTitle = this.getAttribute('data-doc-title');
                window.location.href = `/generate?topic=${encodeURIComponent(docTitle)}`;
            });
        });
    }
    
    // Function to search documents
    function searchDocuments(query) {
        if (!documentsTable) return;
        
        query = query.toLowerCase().trim();
        
        // Get all table rows except the header
        const rows = documentsTable.querySelectorAll('tbody tr');
        
        if (query === '') {
            // If search is empty, show all rows
            rows.forEach(row => {
                row.style.display = '';
            });
            return;
        }
        
        // Filter rows
        rows.forEach(row => {
            const title = row.cells[0].textContent.toLowerCase();
            const type = row.cells[1].textContent.toLowerCase();
            const file = row.cells[2].textContent.toLowerCase();
            
            if (title.includes(query) || type.includes(query) || file.includes(query)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
    
    // Function to view document details
    function viewDocument(docId) {
        // Show document preview modal
        const modal = new bootstrap.Modal(document.getElementById('documentPreviewModal'));
        modal.show();
        
        // Show loading indicator
        document.getElementById('documentPreviewLoading').style.display = 'block';
        document.getElementById('documentPreviewContent').style.display = 'none';
        
        // In a real implementation, we would fetch document details from the API
        // For this demo, we'll simulate a response after a delay
        setTimeout(() => {
            document.getElementById('documentPreviewLoading').style.display = 'none';
            document.getElementById('documentPreviewContent').style.display = 'block';
            
            // Find document details from the table
            const docRow = document.querySelector(`.view-doc-btn[data-doc-id="${docId}"]`).closest('tr');
            const title = docRow.cells[0].textContent;
            const type = docRow.cells[1].textContent;
            const filename = docRow.cells[2].textContent;
            
            // Update modal with document details
            document.getElementById('previewTitle').textContent = title;
            document.getElementById('previewType').textContent = type;
            document.getElementById('previewFilename').textContent = filename;
            
            // Set up the "Use for Generation" button
            document.getElementById('useForGenerationBtn').onclick = function() {
                window.location.href = `/generate?topic=${encodeURIComponent(title)}&content_type=${encodeURIComponent(type.trim())}`;
            };
            
            // Mock document chunks
            document.getElementById('previewChunks').innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> This is where document chunks would be displayed.
                    In a full implementation, this would fetch the actual chunks from the backend.
                </div>
            `;
        }, 1000);
    }
    
    // Function to load generated content
    function loadGeneratedContent() {
        if (!generatedContentList) return;
        
        // Make API request to get generated content
        fetch('/api/list_contents')
            .then(response => response.json())
            .then(data => {
                if (data.length === 0) {
                    generatedContentList.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> You haven't generated any content yet.
                        </div>
                    `;
                    return;
                }
                
                // Limit to 5 most recent items
                const recentContents = data.slice(0, 5);
                
                // Build list items
                let listHtml = '';
                recentContents.forEach(content => {
                    // Format validation badge
                    let validationBadge = '';
                    if (content.validation_score !== null) {
                        const score = Math.round(content.validation_score * 100);
                        let badgeClass = 'bg-success';
                        if (score < 70) badgeClass = 'bg-danger';
                        else if (score < 85) badgeClass = 'bg-warning';
                        
                        validationBadge = `<span class="badge ${badgeClass}">${score}%</span>`;
                    }
                    
                    listHtml += `
                        <a href="/content/${content.id}" class="list-group-item list-group-item-action">
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1">${content.title}</h6>
                                ${validationBadge}
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <small>${content.content_type}</small>
                                <small class="text-muted">${formatDate(content.created_at)}</small>
                            </div>
                        </a>
                    `;
                });
                
                generatedContentList.innerHTML = listHtml;
            })
            .catch(error => {
                console.error('Error loading generated content:', error);
                generatedContentList.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-circle"></i> Error loading content.
                        Please refresh the page to try again.
                    </div>
                `;
            });
    }
    
    // Helper function to format dates
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-NZ', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
});
