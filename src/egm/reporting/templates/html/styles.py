# File Path: src/egm/reporting/templates/html/styles.py
# This is the correct file and location.

# This file holds the CSS for our HTML reports as a Python string.
# This allows us to import it directly into our generator and inject it
# into the template, creating a single, self-contained HTML file.

CSS_STYLES = """
/*
  This CSS content will be used for the generated report.
  Even if the styles.css file is empty, defining this variable
  with some default styles is a good practice.
*/
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #212529;
    background-color: #f8f9fa;
    margin: 0;
    padding: 0;
}
.container {
    max-width: 1024px;
    margin: 20px auto;
    background: #ffffff;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
h1, h2, h3 {
    color: #0056b3;
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 10px;
    margin-top: 1.5em;
    margin-bottom: 1em;
}
h1 {
    font-size: 2.2em;
}
h2 {
    font-size: 1.8em;
}
.plot-container img {
    max-width: 100%;
    height: auto;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    display: block;
    margin: 1em auto;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
th, td {
    padding: 12px 15px;
    text-align: left;
    border-bottom: 1px solid #dee2e6;
}
th {
    background-color: #f2f2f2;
    font-weight: 600;
}
tbody tr:nth-of-type(even) {
    background-color: #f8f9fa;
}
tbody tr:hover {
    background-color: #e9ecef;
}
.metadata-section, .notes-section {
    background-color: #f8f9fa;
    padding: 15px;
    border: 1px solid #e9ecef;
    border-radius: 5px;
    margin-top: 20px;
    font-size: 0.9em;
    word-wrap: break-word;
}
.tag {
    display: inline-block;
    background-color: #007bff;
    color: white;
    padding: 4px 10px;
    border-radius: 15px;
    font-size: 0.8em;
    margin: 2px;
}
footer {
    text-align: center;
    margin-top: 30px;
    padding-top: 20px;
    font-size: 0.85em;
    color: #6c757d;
    border-top: 1px solid #e9ecef;
}
/* Responsive design for narrow screens */
@media (max-width: 768px) {
    .container {
        padding: 1rem;
    }
    h1 {
        font-size: 1.8em;
    }
    h2 {
        font-size: 1.5em;
    }
    th, td {
        padding: 8px 10px;
    }
}
"""