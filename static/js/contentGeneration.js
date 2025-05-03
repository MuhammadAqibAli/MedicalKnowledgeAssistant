document.addEventListener('DOMContentLoaded', function() {
    const generateForm = document.getElementById('generateForm');
    const searchDocumentsBtn = document.getElementById('searchDocumentsBtn');
    const generateBtn = document.getElementById('generateBtn');
    const useRagCheckbox = document.getElementById('use_rag');
    const ragStatusBox = document.getElementById('ragStatusBox');
    const ragStatusText = document.getElementById('ragStatusText');
    const ragProgress = document.getElementById('ragProgress');
    
    if (!generateForm || !searchDocumentsBtn || !generateBtn || !useRagCheckbox) return;
    
    // Handle search for relevant documents
    searchDocumentsBtn.addEventListener('click', function() {
        const topic = document.getElementById('topic').value;
        const contentType = document.getElementById('content_type').value;
        
        if (!topic) {
            alert('Please enter a topic to search for relevant documents.');
            return;
        }
        
        // Show searching status
        ragStatusBox.style.display = 'block';
        ragStatusText.innerHTML = 'Searching for relevant documents...';
        ragProgress.style.width = '100%';
        ragProgress.classList.add('bg-info');
        
        // Disable search button
        searchDocumentsBtn.disabled = true;
        searchDocumentsBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Searching...';
        
        // Make API request to search for documents
        fetch('/api/search_documents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: topic,
                doc_type: contentType
            })
        })
        .then(response => response.json())
        .then(data => {
            // Update status box
            if (data.has_context) {
                ragStatusText.innerHTML = `
                    <div class="mb-2">
                        <i class="fas fa-check-circle text-success"></i> Found ${data.document_count} relevant documents!
                    </div>
                    <div class="small text-muted">${data.context_preview}</div>
                `;
                ragProgress.style.width = '100%';
                ragProgress.classList.remove('bg-info');
                ragProgress.classList.add('bg-success');
                
                // Ensure RAG is enabled
                useRagCheckbox.checked = true;
            } else {
                ragStatusText.innerHTML = `
                    <div class="mb-2">
                        <i class="fas fa-info-circle text-warning"></i> No relevant documents found.
                    </div>
                    <div class="small text-muted">The system will use the LLM's built-in knowledge instead.</div>
                `;
                ragProgress.style.width = '100%';
                ragProgress.classList.remove('bg-info');
                ragProgress.classList.add('bg-warning');
            }
        })
        .catch(error => {
            ragStatusText.innerHTML = `
                <div class="mb-2">
                    <i class="fas fa-exclamation-circle text-danger"></i> Error searching for documents.
                </div>
                <div class="small text-muted">Please try again or proceed with generation without RAG.</div>
            `;
            ragProgress.style.width = '100%';
            ragProgress.classList.remove('bg-info');
            ragProgress.classList.add('bg-danger');
            
            console.error('Error searching for documents:', error);
        })
        .finally(() => {
            // Re-enable search button
            searchDocumentsBtn.disabled = false;
            searchDocumentsBtn.innerHTML = '<i class="fas fa-search"></i> Check for Relevant Documents';
        });
    });
    
    // Handle RAG checkbox change
    useRagCheckbox.addEventListener('change', function() {
        if (!this.checked) {
            ragStatusBox.style.display = 'none';
        } else {
            // If we already searched, show the status box
            if (ragStatusText.innerHTML !== 'Searching for relevant documents...') {
                ragStatusBox.style.display = 'block';
            }
        }
    });
    
    // Handle form submission
    generateForm.addEventListener('submit', function(e) {
        const topic = document.getElementById('topic').value;
        const contentType = document.getElementById('content_type').value;
        
        if (!topic.trim()) {
            e.preventDefault();
            alert('Please enter a topic for content generation.');
            return;
        }
        
        if (!contentType) {
            e.preventDefault();
            alert('Please select a content type.');
            return;
        }
        
        // Show loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        
        // Form will submit normally if all validations pass
    });
    
    // Handle URL parameters for pre-filling the form
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('topic')) {
        document.getElementById('topic').value = urlParams.get('topic');
    }
    
    if (urlParams.has('content_type')) {
        const contentType = urlParams.get('content_type');
        const contentTypeSelect = document.getElementById('content_type');
        
        // Find and select the matching option
        for (let i = 0; i < contentTypeSelect.options.length; i++) {
            if (contentTypeSelect.options[i].value === contentType) {
                contentTypeSelect.selectedIndex = i;
                break;
            }
        }
    }
});
