from flask import Flask, render_template, request, jsonify
import os
import time
import re
from dotenv import load_dotenv
from main import answer_question
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for all routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Process the question - simple and direct
        raw_answer = answer_question(question)
        
        # Format the answer into sections
        formatted_answer = format_answer(raw_answer)
        
        return jsonify(formatted_answer)
        
    except Exception as e:
        print(f"Error in /ask endpoint: {str(e)}")
        return jsonify({'error': str(e), 'answer': 'An error occurred while processing your request.'}), 500

def format_answer(raw_answer):
    """Format the raw answer into structured sections for better display"""
    # Initialize result structure
    result = {
        'main_answer': '',
        'follow_up_questions': [],
        'read_more': []
    }
    
    # Check for "Follow-up questions" or similar patterns
    follow_up_patterns = [
        r'Follow-up questions(?: to explore next)?:',
        r'Follow-up Questions:',
        r'Additional questions you might be interested in:',
        r'You might also want to know:'
    ]
    
    # Check for "Read more" or similar patterns
    read_more_patterns = [
        r'Read more:',
        r'Read More:',
        r'Sources:',
        r'References:'
    ]
    
    # Combine patterns
    combined_follow_up_pattern = '|'.join(follow_up_patterns)
    combined_read_more_pattern = '|'.join(read_more_patterns)
    
    # Extract main answer, follow-up and read more sections
    main_answer = raw_answer
    
    # Search for follow-up questions section
    follow_up_match = re.search(f'({combined_follow_up_pattern})(.*?)(?:{combined_read_more_pattern}|$)', 
                                raw_answer, re.DOTALL)
    
    read_more_match = re.search(f'({combined_read_more_pattern})(.*?)$', raw_answer, re.DOTALL)
    
    # Extract follow-up questions if found
    if follow_up_match:
        # Update main answer to exclude follow-up
        main_answer_end = follow_up_match.start()
        main_answer = raw_answer[:main_answer_end].strip()
        
        # Extract follow-up questions text
        follow_up_text = follow_up_match.group(2).strip()
        
        # Parse numbered items
        questions = []
        for line in follow_up_text.split('\n'):
            line = line.strip()
            # Match patterns like "1. Question" or "1) Question" or just a question
            if re.match(r'^\d+[\.\)]', line):
                question = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                if question:
                    questions.append(question)
        
        result['follow_up_questions'] = questions
    
    # Extract read more links if found
    if read_more_match:
        # If we didn't find follow-up but found read-more
        if not follow_up_match:
            main_answer_end = read_more_match.start()
            main_answer = raw_answer[:main_answer_end].strip()
        
        read_more_text = read_more_match.group(2).strip()
        
        # Parse links - could be URLs or titles
        links = []
        for line in read_more_text.split('\n'):
            line = line.strip()
            if line:
                # Try to extract URLs if present
                url_match = re.search(r'(https?://\S+)', line)
                if url_match:
                    url = url_match.group(1)
                    # Try to extract title
                    title = line.replace(url, '').strip()
                    if not title:
                        title = url
                    
                    # Clean up the title
                    title = title.strip('- []()').strip()
                    
                    links.append({'url': url, 'title': title})
                elif line:  # Just a title without URL
                    links.append({'url': '#', 'title': line})
        
        result['read_more'] = links
    
    # Set the main answer
    result['main_answer'] = main_answer
    
    return result

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create templates/index.html with a modern version
    with open('templates/index.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>RAG Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2563eb;
            --text-color: #1f2937;
            --bg-color: #f9fafb;
            --card-bg: #ffffff;
            --border-color: #e5e7eb;
            --hover-color: #dbeafe;
        }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            color: var(--text-color);
            background-color: var(--bg-color);
        }
        .container {
            max-width: 1000px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        header {
            background-color: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            padding: 2rem;
            margin-bottom: 2rem;
        }
        h1 {
            color: var(--primary-color);
            margin: 0;
            font-size: 2.2rem;
            font-weight: 600;
        }
        .subtitle {
            color: #6b7280;
            margin-top: 0.5rem;
            font-weight: 400;
        }
        .search-container {
            display: flex;
            margin-bottom: 1.5rem;
        }
        #question-input {
            flex: 1;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            border: 1px solid var(--border-color);
            border-radius: 8px 0 0 8px;
            font-family: inherit;
        }
        #search-button {
            padding: 0 1.5rem;
            background-color: var(--primary-color);
            color: white;
            font-weight: 500;
            border: none;
            border-radius: 0 8px 8px 0;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        #search-button:hover {
            background-color: #1d4ed8;
        }
        #loading {
            display: none;
            padding: 3rem 0;
            text-align: center;
        }
        .spinner {
            display: inline-block;
            width: 50px;
            height: 50px;
            border: 5px solid rgba(37, 99, 235, 0.2);
            border-radius: 50%;
            border-top-color: var(--primary-color);
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        #answer-container {
            display: none;
            background-color: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-top: 1.5rem;
            overflow: hidden;
        }
        .answer-header {
            background-color: #f3f4f6;
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }
        .answer-header h2 {
            margin: 0;
            font-weight: 600;
            font-size: 1.25rem;
            color: var(--text-color);
        }
        .answer-content {
            padding: 1.5rem;
        }
        #answer-text {
            line-height: 1.8;
            margin-bottom: 2rem;
            white-space: pre-wrap;
        }
        .section {
            margin-top: 2.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
        }
        .section h3 {
            font-size: 1.1rem;
            color: var(--text-color);
            margin-top: 0;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        .follow-up {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        .follow-up button {
            padding: 0.7rem 1.2rem;
            background-color: #f3f4f6;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            border-radius: 2rem;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }
        .follow-up button:hover {
            background-color: var(--hover-color);
            border-color: #bfdbfe;
        }
        .read-more a {
            display: block;
            padding: 0.75rem 1rem;
            color: var(--primary-color);
            text-decoration: none;
            border-radius: 6px;
            margin-bottom: 0.5rem;
            transition: all 0.2s;
            font-size: 0.95rem;
        }
        .read-more a:hover {
            background-color: var(--hover-color);
        }
        .read-more a::before {
            content: '🔗';
            margin-right: 0.5rem;
        }
        
        /* Responsive styling */
        @media (max-width: 768px) {
            .container {
                margin: 1rem auto;
            }
            header {
                padding: 1.5rem;
            }
            h1 {
                font-size: 1.8rem;
            }
        }
        
        /* Dark mode toggle */
        .theme-toggle {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            color: var(--text-color);
            cursor: pointer;
            font-size: 1.5rem;
            opacity: 0.7;
            transition: opacity 0.2s;
        }
        .theme-toggle:hover {
            opacity: 1;
        }
        
        /* Dark mode styles */
        .dark-mode {
            --primary-color: #3b82f6;
            --text-color: #f9fafb;
            --bg-color: #111827;
            --card-bg: #1f2937;
            --border-color: #374151;
            --hover-color: #1e3a8a;
        }
    </style>
</head>
<body>
    <button class="theme-toggle" id="theme-toggle">🌓</button>
    
    <div class="container">
        <header>
            <h1>🔍 RAG Assistant</h1>
            <p class="subtitle">Ask a question to get comprehensive, reliable answers with sources</p>
        
            <div class="search-container">
                <input type="text" id="question-input" placeholder="Enter your question..." autofocus>
                <button id="search-button">Search</button>
            </div>
        </header>
        
        <div id="loading">
            <div class="spinner"></div>
            <p>Searching for the most up-to-date information...</p>
        </div>
        
        <div id="answer-container">
            <div class="answer-header">
                <h2>Answer</h2>
            </div>
            
            <div class="answer-content">
                <div id="answer-text"></div>
                
                <div class="section">
                    <h3>Follow-up questions</h3>
                    <div id="follow-up-questions" class="follow-up"></div>
                </div>
                
                <div class="section">
                    <h3>Read more</h3>
                    <div id="read-more-links" class="read-more"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Theme toggler
        const themeToggle = document.getElementById('theme-toggle');
        const body = document.body;
        
        // Check for saved theme preference or use device preference
        const savedTheme = localStorage.getItem('theme') || 
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        
        if (savedTheme === 'dark') {
            body.classList.add('dark-mode');
        }
        
        themeToggle.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            const currentTheme = body.classList.contains('dark-mode') ? 'dark' : 'light';
            localStorage.setItem('theme', currentTheme);
        });
        
        // Search functionality
        document.getElementById('search-button').addEventListener('click', function() {
            const question = document.getElementById('question-input').value.trim();
            if (!question) return;
            
            // Show loading, hide results
            document.getElementById('loading').style.display = 'block';
            document.getElementById('answer-container').style.display = 'none';
            
            // Make the request
            fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Format main answer with Markdown-like enhancements
                const mainAnswer = formatText(data.main_answer || '');
                document.getElementById('answer-text').innerHTML = mainAnswer;
                
                // Add follow-up questions
                const followUpContainer = document.getElementById('follow-up-questions');
                followUpContainer.innerHTML = '';
                
                if (data.follow_up_questions && data.follow_up_questions.length) {
                    data.follow_up_questions.forEach(question => {
                        const button = document.createElement('button');
                        button.textContent = question;
                        button.addEventListener('click', function() {
                            document.getElementById('question-input').value = question;
                            document.getElementById('search-button').click();
                        });
                        followUpContainer.appendChild(button);
                    });
                } else {
                    followUpContainer.innerHTML = '<p>No follow-up questions available</p>';
                }
                
                // Add read more links
                const readMoreContainer = document.getElementById('read-more-links');
                readMoreContainer.innerHTML = '';
                
                if (data.read_more && data.read_more.length) {
                    data.read_more.forEach(item => {
                        const link = document.createElement('a');
                        link.href = item.url;
                        link.textContent = item.title || item.url;
                        link.target = '_blank';
                        link.rel = 'noopener noreferrer';
                        readMoreContainer.appendChild(link);
                    });
                } else {
                    readMoreContainer.innerHTML = '<p>No additional resources available</p>';
                }
                
                // Hide loading, show results
                document.getElementById('loading').style.display = 'none';
                document.getElementById('answer-container').style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('answer-text').innerHTML = 
                    `<div class="error">Error: ${error.message}<br>Please try again.</div>`;
                document.getElementById('loading').style.display = 'none';
                document.getElementById('answer-container').style.display = 'block';
            });
        });
        
        // Handle Enter key in the input field
        document.getElementById('question-input').addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                document.getElementById('search-button').click();
            }
        });
        
        // Simple Markdown-like formatter
        function formatText(text) {
            if (!text) return '';
            
            // Bold text **example**
            text = text.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
            
            // Italics *example*
            text = text.replace(/\\*([^*]+)\\*/g, '<em>$1</em>');
            
            // Source citation
            text = text.replace(/\\[Source\\s+(\\d+)\\]/g, '<span class="source">[Source $1]</span>');
            
            // Process paragraphs
            let paragraphs = text.split(/\\n\\n+/);
            let processedHtml = '';
            
            for (let p of paragraphs) {
                p = p.trim();
                if (!p) continue;
                
                // Check if this is a numbered list
                if (/^\\d+\\.\\s/.test(p)) {
                    const listItems = p.split(/\\n/).filter(line => /^\\d+\\.\\s/.test(line));
                    if (listItems.length > 0) {
                        let listHtml = '<ol>';
                        for (const item of listItems) {
                            const content = item.replace(/^\\d+\\.\\s/, '').trim();
                            listHtml += `<li>${content}</li>`;
                        }
                        listHtml += '</ol>';
                        processedHtml += listHtml;
                    } else {
                        processedHtml += `<p>${p}</p>`;
                    }
                } else {
                    processedHtml += `<p>${p}</p>`;
                }
            }
            
            return processedHtml || text;
        }
    </script>
</body>
</html>
        ''')
    
    # Run the app with specific host and port settings
    print("Starting server at http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)