// Run with: node build-standalone.js
// Creates AH-QUESTIONS-standalone.html - single file with all CSS/JS inline

const fs = require('fs');
const path = require('path');

const dir = __dirname;

const css = fs.readFileSync(path.join(dir, 'styles.css'), 'utf8');
const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');

const scripts = [
  'questions.js',
  'flight_planning_set2.js',
  'radio_navigation_set3.js',
  'meteorology_set4.js',
  'app.js'
];

let jsContent = '';
for (const file of scripts) {
  const p = path.join(dir, file);
  if (fs.existsSync(p)) {
    jsContent += fs.readFileSync(p, 'utf8') + '\n';
  }
}

// Build standalone: replace stylesheet and scripts with inline content
let out = html.replace(/<link rel="stylesheet" href="styles\.css">/, '<style>\n' + css + '\n</style>');
out = out.replace(/<script src="questions\.js"><\/script>[\s\S]*?<script src="app\.js"><\/script>/, '<script>\n' + jsContent + '\n</script>');

const outPath = path.join(dir, 'AH-QUESTIONS-standalone.html');
fs.writeFileSync(outPath, out, 'utf8');
console.log('Created: AH-QUESTIONS-standalone.html');
console.log('Size:', (fs.statSync(outPath).size / 1024).toFixed(1), 'KB');
