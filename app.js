(function () {
  const landing = document.getElementById('landing');
  const quizSection = document.getElementById('quiz-section');
  const resultsSection = document.getElementById('results-section');
  const startBtn = document.getElementById('start-btn');
  const restartBtn = document.getElementById('restart-btn');
  const questionText = document.getElementById('question-text');
  const optionsContainer = document.getElementById('options');
  const currentNumEl = document.getElementById('current-num');
  const totalNumEl = document.getElementById('total-num');
  const scoreEl = document.getElementById('score');
  const backToHomeBtn = document.getElementById('back-to-home-btn');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const finalScoreEl = document.getElementById('final-score');
  const finalTotalEl = document.getElementById('final-total');
  const percentEl = document.getElementById('percent');

  const shuffleCheckbox = document.getElementById('shuffle-questions');
  let currentQuestions = [];
  let total = 0;
  let currentIndex = 0;
  let userAnswers = [];

  function shuffleArray(arr) {
    var copy = arr.slice();
    for (var i = copy.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = copy[i];
      copy[i] = copy[j];
      copy[j] = t;
    }
    return copy;
  }

  function setSectionVisibility(showEl, hideEl1, hideEl2) {
    showEl.classList.remove('hidden');
    showEl.removeAttribute('hidden');
    hideEl1.classList.add('hidden');
    hideEl1.setAttribute('hidden', '');
    hideEl2.classList.add('hidden');
    hideEl2.setAttribute('hidden', '');
  }

  function showLanding() {
    setSectionVisibility(landing, quizSection, resultsSection);
  }

  function showQuiz() {
    setSectionVisibility(quizSection, landing, resultsSection);
  }

  function showResults() {
    setSectionVisibility(resultsSection, landing, quizSection);
    const correctCount = currentQuestions.reduce(function (count, q, i) {
      return count + (userAnswers[i] === q.correct ? 1 : 0);
    }, 0);
    finalScoreEl.textContent = correctCount;
    finalTotalEl.textContent = total;
    percentEl.textContent = total ? Math.round((correctCount / total) * 100) : 0;
  }

  function renderQuestion() {
    const q = currentQuestions[currentIndex];
    const answered = userAnswers[currentIndex] >= 0;
    currentNumEl.textContent = currentIndex + 1;
    totalNumEl.textContent = total;
    var qText = (q && (q.question || q.text || '')) || '(Question not available)';
    questionText.textContent = qText;

    optionsContainer.innerHTML = '';
    const letters = ['A', 'B', 'C', 'D'];
    var opts = Array.isArray(q.options) ? q.options : [];
    opts.forEach(function (opt, i) {
      const label = document.createElement('label');
      var optClass = 'option';
      if (answered) {
        if (i === q.correct) optClass += ' correct';
        if (i === userAnswers[currentIndex] && i !== q.correct) optClass += ' wrong';
        if (i === userAnswers[currentIndex]) optClass += ' selected';
      } else if (userAnswers[currentIndex] === i) {
        optClass += ' selected';
      }
      label.className = optClass;
      label.innerHTML = '<span class="option-letter">' + letters[i] + '</span><span>' + opt + '</span>';
      if (!answered) {
        var selectOption = function () {
          userAnswers[currentIndex] = i;
          document.querySelectorAll('#options .option').forEach(function (el) {
            el.classList.remove('selected', 'correct', 'wrong');
          });
          label.classList.add('selected');
          var opts = optionsContainer.querySelectorAll('.option');
          opts[q.correct].classList.add('correct');
          if (i !== q.correct) label.classList.add('wrong');
          updateScoreDisplay();
        };
        label.addEventListener('click', selectOption);
        label.addEventListener('touchend', function (e) {
          e.preventDefault();
          selectOption();
        }, { passive: false });
      }
      optionsContainer.appendChild(label);
    });

    if (currentIndex === 0) {
      if (backToHomeBtn) backToHomeBtn.classList.remove('hidden');
      prevBtn.classList.add('hidden');
      prevBtn.disabled = true;
    } else {
      if (backToHomeBtn) backToHomeBtn.classList.add('hidden');
      prevBtn.classList.remove('hidden');
      prevBtn.disabled = false;
    }
    if (currentIndex === total - 1) {
      nextBtn.textContent = 'Finish';
    } else {
      nextBtn.textContent = 'Next';
    }
  }

  function updateScoreDisplay() {
    let correctCount = 0;
    for (let i = 0; i <= currentIndex; i++) {
      if (userAnswers[i] === currentQuestions[i].correct) correctCount++;
    }
    scoreEl.textContent = correctCount + ' / ' + (currentIndex + 1);
  }

  function goNext() {
    if (currentIndex === total - 1) {
      showResults();
      return;
    }
    currentIndex++;
    renderQuestion();
    updateScoreDisplay();
  }

  function goPrev() {
    if (currentIndex === 0) return;
    currentIndex--;
    renderQuestion();
    updateScoreDisplay();
  }

  function isValidQuestion(q) {
    if (!q || typeof q !== 'object') return false;
    var text = (q.question || q.text || '').trim();
    if (!text || !Array.isArray(q.options) || q.options.length === 0) return false;
    if (/^Question\s+\d+$/i.test(text)) return false;
    return true;
  }

  function filterValid(questions) {
    return (questions || []).filter(isValidQuestion);
  }

  function getMergedQuestions() {
    var set1 = typeof QUIZ_QUESTIONS !== 'undefined' ? QUIZ_QUESTIONS : [];
    var set2 = typeof QUIZ_QUESTIONS_SET2 !== 'undefined' ? QUIZ_QUESTIONS_SET2 : [];
    var set3 = typeof QUIZ_QUESTIONS_SET3 !== 'undefined' ? QUIZ_QUESTIONS_SET3 : [];
    var set4 = typeof QUIZ_QUESTIONS_SET4 !== 'undefined' ? QUIZ_QUESTIONS_SET4 : [];
    return filterValid(set1.slice().concat(set2).concat(set3).concat(set4));
  }

  function getSourceForCustom(sourceValue) {
    var raw;
    if (sourceValue === '4' && typeof QUIZ_QUESTIONS_SET4 !== 'undefined') raw = QUIZ_QUESTIONS_SET4.slice();
    else if (sourceValue === '3' && typeof QUIZ_QUESTIONS_SET3 !== 'undefined') raw = QUIZ_QUESTIONS_SET3.slice();
    else if (sourceValue === '2' && typeof QUIZ_QUESTIONS_SET2 !== 'undefined') raw = QUIZ_QUESTIONS_SET2.slice();
    else if (sourceValue === '1' && typeof QUIZ_QUESTIONS !== 'undefined') raw = QUIZ_QUESTIONS.slice();
    else raw = getMergedQuestions();
    return filterValid(raw);
  }

  function updateCustomQuizMax() {
    if (!customCountInput) return;
    var sourceSelect = document.getElementById('custom-quiz-source');
    var sourceVal = sourceSelect ? sourceSelect.value : 'all';
    var pool = getSourceForCustom(sourceVal);
    var maxQ = Math.max(1, pool.length);
    customCountInput.max = maxQ;
    if (parseInt(customCountInput.value, 10) > maxQ) customCountInput.value = maxQ;
  }

  var setSelect = document.getElementById('question-set');
  var customOptions = document.getElementById('custom-quiz-options');
  var customCountInput = document.getElementById('custom-quiz-count');
  var customSourceSelect = document.getElementById('custom-quiz-source');

  if (typeof QUIZ_QUESTIONS_SET2 === 'undefined' && customSourceSelect) {
    var opt2 = customSourceSelect.querySelector('option[value="2"]');
    if (opt2) opt2.disabled = true;
  }

  function toggleCustomOptions() {
    if (!setSelect || !customOptions) return;
    if (setSelect.value === 'custom') {
      customOptions.classList.remove('hidden');
      updateCustomQuizMax();
    } else {
      customOptions.classList.add('hidden');
    }
  }
  if (setSelect && customOptions && customCountInput) {
    setSelect.addEventListener('change', toggleCustomOptions);
    setSelect.addEventListener('input', toggleCustomOptions);
  }
  if (customSourceSelect && customCountInput) {
    customSourceSelect.addEventListener('change', updateCustomQuizMax);
  }

  addTouchClick(startBtn, function () {
    var setValue = setSelect ? setSelect.value : '1';
    var source;
    if (setValue === 'custom') {
      var sourceVal = customSourceSelect ? customSourceSelect.value : 'all';
      source = getSourceForCustom(sourceVal);
      if (source.length === 0) source = filterValid(typeof QUIZ_QUESTIONS !== 'undefined' ? QUIZ_QUESTIONS.slice() : []);
      var n = Math.max(1, Math.min(source.length, parseInt(customCountInput && customCountInput.value, 10) || 20));
      source = shuffleCheckbox && shuffleCheckbox.checked ? shuffleArray(source) : source.slice();
      currentQuestions = source.slice(0, n);
    } else {
      if (setValue === '4' && typeof QUIZ_QUESTIONS_SET4 !== 'undefined') source = QUIZ_QUESTIONS_SET4;
      else if (setValue === '3' && typeof QUIZ_QUESTIONS_SET3 !== 'undefined') source = QUIZ_QUESTIONS_SET3;
      else if (setValue === '2' && typeof QUIZ_QUESTIONS_SET2 !== 'undefined') source = QUIZ_QUESTIONS_SET2;
      else source = QUIZ_QUESTIONS;
      source = filterValid(shuffleCheckbox && shuffleCheckbox.checked ? shuffleArray(source) : source.slice());
      currentQuestions = source;
    }
    total = currentQuestions.length;
    if (total === 0) return;
    userAnswers = new Array(total).fill(-1);
    currentIndex = 0;
    showQuiz();
    renderQuestion();
    scoreEl.textContent = '0 / 1';
  });

  addTouchClick(restartBtn, function () {
    userAnswers = new Array(total).fill(-1);
    currentIndex = 0;
    showQuiz();
    renderQuestion();
    scoreEl.textContent = '0 / 1';
  });

  function addTouchClick(el, handler) {
    if (!el) return;
    var lastTouch = 0;
    el.addEventListener('click', function (e) {
      if (Date.now() - lastTouch < 400) return;
      handler(e);
    });
    el.addEventListener('touchend', function (e) {
      lastTouch = Date.now();
      e.preventDefault();
      handler(e);
    }, { passive: false });
  }

  if (backToHomeBtn) addTouchClick(backToHomeBtn, showLanding);
  addTouchClick(prevBtn, goPrev);
  addTouchClick(nextBtn, goNext);

  document.addEventListener('keydown', function (e) {
    if (quizSection.classList.contains('hidden')) return;
    var q = currentQuestions[currentIndex];
    var answered = q && userAnswers[currentIndex] >= 0;
    var key = e.key.toLowerCase();
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      goNext();
      return;
    }
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      goPrev();
      return;
    }
    if (key === 'a' || key === 'b' || key === 'c' || key === 'd') {
      var optionIndex = key.charCodeAt(0) - 97;
      if (answered || !q || optionIndex >= q.options.length) return;
      e.preventDefault();
      userAnswers[currentIndex] = optionIndex;
      renderQuestion();
      updateScoreDisplay();
    }
  });

  var setCount = (setSelect && setSelect.value === '4' && typeof QUIZ_QUESTIONS_SET4 !== 'undefined')
    ? QUIZ_QUESTIONS_SET4.length
    : (setSelect && setSelect.value === '3' && typeof QUIZ_QUESTIONS_SET3 !== 'undefined')
    ? QUIZ_QUESTIONS_SET3.length
    : (setSelect && setSelect.value === '2' && typeof QUIZ_QUESTIONS_SET2 !== 'undefined')
    ? QUIZ_QUESTIONS_SET2.length
    : (typeof QUIZ_QUESTIONS !== 'undefined' ? QUIZ_QUESTIONS.length : 0);
  totalNumEl.textContent = setCount;
  if (setSelect) setSelect.addEventListener('change', function () {
    if (setSelect.value === 'custom') return;
    var c = (setSelect.value === '4' && typeof QUIZ_QUESTIONS_SET4 !== 'undefined') ? QUIZ_QUESTIONS_SET4.length
      : (setSelect.value === '3' && typeof QUIZ_QUESTIONS_SET3 !== 'undefined') ? QUIZ_QUESTIONS_SET3.length
      : (setSelect.value === '2' && typeof QUIZ_QUESTIONS_SET2 !== 'undefined') ? QUIZ_QUESTIONS_SET2.length
      : (typeof QUIZ_QUESTIONS !== 'undefined' ? QUIZ_QUESTIONS.length : 0);
    totalNumEl.textContent = c;
  });
})();
