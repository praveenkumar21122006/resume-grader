const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const resumeText = document.getElementById('resumeText');
const jdText = document.getElementById('jdText');
const gradeBtn = document.getElementById('gradeBtn');
const errorMsg = document.getElementById('errorMsg');
const loadingMsg = document.getElementById('loadingMsg');
const resultPanel = document.getElementById('resultPanel');
const emptyPanel = document.getElementById('emptyPanel');

let selectedFile = null;

// Drop zone
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault(); dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => { if (fileInput.files.length) handleFile(fileInput.files[0]); });

function handleFile(file){
  const allowed = ['.pdf','.docx','.doc','.txt'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if(!allowed.includes(ext) && !file.type.includes('pdf') && !file.type.includes('word') && file.type !== 'text/plain'){
    // still allow but warn
  }
  if(file.size > 5*1024*1024){ errorMsg.textContent = 'File too large — max 5MB.'; return; }
  selectedFile = file;
  fileName.textContent = `📄 ${file.name} (${(file.size/1024).toFixed(0)} KB)`;
  errorMsg.textContent = '';
}

gradeBtn.addEventListener('click', async () => {
  errorMsg.textContent = '';
  const text = resumeText.value.trim();
  const jd = jdText.value.trim();
  if(!selectedFile && !text){
    errorMsg.textContent = 'Please upload a resume file or paste resume text.';
    return;
  }
  gradeBtn.disabled = true;
  gradeBtn.textContent = 'Grading…';
  loadingMsg.style.display = 'block';
  resultPanel.style.display = 'none';
  emptyPanel.style.display = 'none';

  try{
    let res, data;
    if(selectedFile){
      const fd = new FormData();
      fd.append('file', selectedFile);
      if(text) fd.append('text', text);
      if(jd) fd.append('job_description', jd);
      res = await fetch('/api/grade', { method:'POST', body: fd });
      data = await res.json();
    } else {
      res = await fetch('/api/grade-text', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ text, job_description: jd })
      });
      data = await res.json();
    }
    if(!res.ok) throw new Error(data.error || 'Grading failed');
    renderResult(data);
  } catch(e){
    errorMsg.textContent = e.message;
    emptyPanel.style.display = '';
  } finally {
    gradeBtn.disabled = false;
    gradeBtn.textContent = '⚡ Grade Resume';
    loadingMsg.style.display = 'none';
  }
});

function renderResult(data){
  const g = data.grading;
  const m = data.matching;
  const p = data.parsed;
  const br = g.breakdown;

  const barColor = (pct) => pct>=80 ? '#10b981' : pct>=60 ? '#84cc16' : pct>=40 ? '#eab308' : '#ef4444';

  let html = `
    <div class="res-header">
      <div class="res-ring" style="--pct:${g.total}; --color:${g.color}"><span>${g.total}<small>/100</small></span></div>
      <div>
        <h3>Grade ${g.grade} — ${g.level}</h3>
        <p>${g.total>=80?'Excellent — ready to apply!':g.total>=60?'Good foundation, polish suggested':'Needs improvement before applying'}</p>
        <div class="kwd">${p.skills.length} skills • ${p.stats.word_count} words • ${p.stats.bullet_count} bullets</div>
      </div>
    </div>
    <div class="res-stats">
      <div><strong>${p.stats.word_count}</strong>Words</div>
      <div><strong>${p.skills.length}</strong>Skills</div>
      <div><strong>${p.stats.bullet_count}</strong>Bullets</div>
      <div><strong>${g.stats.quantifiable}</strong>Metrics</div>
    </div>
    <div class="breakdown">
      <h4>Score Breakdown</h4>
      ${Object.values(br).map(b=>{
        const pct = Math.round(b.score/b.max*100);
        return `<div class="b-item"><label>${b.label}</label><span>${b.score}/${b.max}</span><div class="b-bar"><div style="width:${pct}%; background:${barColor(pct)}"></div></div></div>`;
      }).join('')}
    </div>
  `;

  if(m && m.similarity_percent !== null){
    html += `
      <div class="match-box">
        <div class="match-head"><h4>📋 JD Match</h4><span class="match-pct">${m.similarity_percent}%</span></div>
        <p style="font-size:.82rem;color:#475569;margin-bottom:8px">${m.verdict}</p>
        <div style="font-size:.78rem;color:#64748b">Keyword coverage: <strong>${m.keyword_coverage}%</strong> (${m.matched_skills.length}/${m.jd_skills.length} JD skills)</div>
        ${m.matched_skills.length? `<div style="font-size:.78rem;margin-top:8px;font-weight:600">✓ Matched</div><div class="chips">${m.matched_skills.map(s=>`<span class="chip ok">${s}</span>`).join('')}</div>` : ''}
        ${m.missing_skills.length? `<div style="font-size:.78rem;margin-top:8px;font-weight:600;color:#991b1b">✗ Missing from resume</div><div class="chips">${m.missing_skills.map(s=>`<span class="chip miss">${s}</span>`).join('')}</div>` : ''}
        ${m.jd_skills.length===0? `<p style="font-size:.78rem;color:#64748b">No standard skills detected in JD — try a more detailed description.</p>`:''}
        ${data.jd_keywords && data.jd_keywords.length? `<div style="margin-top:10px"><div style="font-size:.78rem;font-weight:600">Top JD keywords</div><div class="chips">${data.jd_keywords.map(k=>`<span class="chip neutral">${k}</span>`).join('')}</div></div>`:''}
      </div>
    `;
  } else {
    html += `<div class="match-box"><h4>📋 JD Match</h4><p style="font-size:.82rem;color:#64748b">${m.verdict}</p><p style="font-size:.78rem;color:#94a3b8;margin-top:6px">Tip: paste a job description to get similarity % and missing keywords.</p></div>`;
  }

  html += `
    <div class="suggestions">
      <h4>💡 Suggestions to improve</h4>
      <ul>${g.suggestions.map(s=>`<li>${s}</li>`).join('')}</ul>
      ${g.feedback.length? `<div style="margin-top:10px"><h4>Notes</h4><ul>${g.feedback.map(f=>`<li>${f}</li>`).join('')}</ul></div>`:''}
    </div>
    <div class="parsed-grid">
      <div><span>Email</span><strong>${p.contact.email || '— not found'}</strong></div>
      <div><span>Phone</span><strong>${p.contact.phone || '—'}</strong></div>
      <div><span>LinkedIn</span><strong style="word-break:break-all">${p.contact.linkedin || '—'}</strong></div>
      <div><span>Experience</span><strong>${p.experience_years ? p.experience_years+' yrs (est.)' : '—'}</strong></div>
    </div>
    <div style="padding:0 20px 8px">
      <div style="font-size:.78rem;font-weight:600;margin-bottom:6px">Detected skills (${p.skills.length})</div>
      <div class="chips">${p.skills.length? p.skills.map(s=>`<span class="chip neutral">${s}</span>`).join('') : '<span style="font-size:.82rem;color:#94a3b8">No skills detected — add a Skills section.</span>'}</div>
      <div style="margin-top:10px;font-size:.78rem;color:#64748b">Sections: ${Object.entries(p.sections).filter(([k,v])=>v).map(([k])=>k).join(', ') || 'none detected'}</div>
    </div>
    <div class="preview">
      <h4>Extracted text preview</h4>
      <pre>${escapeHtml(p.preview)}</pre>
    </div>
  `;
  resultPanel.innerHTML = html;
  resultPanel.style.display = '';
  resultPanel.scrollIntoView({ behavior:'smooth', block:'start' });
}

function escapeHtml(s){
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function loadSample(kind){
  if(kind==='strong'){
    resumeText.value = `Alex Johnson
alex.johnson@email.com | +1 (555) 123-4567 | linkedin.com/in/alexjohnson | github.com/alexj

Summary
Results-driven Software Engineer with 4 years experience building scalable web systems in Python, React and AWS. Passionate about clean code and measurable impact.

Experience
Senior Software Engineer — TechCorp, San Francisco | 2021 - Present
• Developed microservices in Python & FastAPI serving 2M+ requests/day, reduced latency by 42%
• Led a team of 5 engineers to migrate monolith to Kubernetes, improved deployment frequency by 3x
• Implemented CI/CD with Docker, Jenkins & AWS, decreased release time by 60%
• Optimized PostgreSQL queries, saving $18k/year in infra costs

Software Engineer — StartupXYZ | 2019 - 2021
• Built React + Node.js dashboard used by 10k+ users, increased retention by 18%
• Created REST APIs and integrated Elasticsearch, improving search speed by 55%
• Mentored 3 junior developers and established agile code review process

Education
B.S. Computer Science — Stanford University | 2015 - 2019 | GPA 3.8

Skills
Python, JavaScript, TypeScript, React, Node.js, FastAPI, Django, PostgreSQL, MongoDB, Redis, AWS, Docker, Kubernetes, Git, CI/CD, Machine Learning, System Design, Agile

Projects
• ResumeGrader NLP — TF-IDF + cosine similarity resume scoring, 92% ATS match
• RealTime Chat — WebSocket scaling to 50k concurrent users

Certifications
AWS Certified Solutions Architect — 2022

Achievements
• Increased user engagement by 32% via A/B testing
• Awarded Employee of the Year 2022
`;
    jdText.value = `We are hiring a Senior Software Engineer (Python/React/AWS).
Must have 3+ years in Python, FastAPI/Django, React, PostgreSQL, Docker, Kubernetes, AWS, CI/CD, microservices, REST APIs, system design. Experience with machine learning is a plus.`;
  } else {
    resumeText.value = `John Doe
john doe email

Objective: Seeking a job

Experience: Did some work at a company. Responsible for various tasks. Worked with computers.

Education: College

Skills: computers, teamwork

I am hardworking and I did my best. I was responsible for many things and I think I am good.`;
    jdText.value = `Senior Software Engineer — Python, React, AWS, Docker, Kubernetes, PostgreSQL, FastAPI, System Design, Machine Learning required.`;
  }
  selectedFile = null;
  fileName.textContent = '';
  fileInput.value = '';
}

function clearAll(){
  resumeText.value = '';
  jdText.value = '';
  selectedFile = null;
  fileName.textContent = '';
  fileInput.value = '';
  resultPanel.style.display = 'none';
  emptyPanel.style.display = '';
  errorMsg.textContent = '';
}
