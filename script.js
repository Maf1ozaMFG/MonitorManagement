// Import MediaPipe's GestureRecognizer and utilities (from CDN)
import { GestureRecognizer, FilesetResolver, DrawingUtils } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3";

class MonitorControlSPA {
  constructor() {
    // State flags
    this.isGestureActive = false;
    this.awaitingConfirmation = false;
    this.currentCommand = null;
    this.lastLoggedGesture = null;  // для отслеживания изменений жеста
    this.placeholderImg = null;   // ссылка на <img>
    // Threshold settings (modifiable via sliders)
    this.gestureThreshold = 0.8;
    this.confidenceThreshold = 0.75;
    // MediaPipe and media elements
    this.gestureRecognizer = null;
    this.videoElement = null;
    this.canvasElement = null;
    this.canvasCtx = null;
    // Gesture tracking for stability
    this.lastGesture = null;
    this.lastGestureTime = 0;
    this.gestureStabilityCount = 0;
    this.currentPairLabel    = null; // хранит строку вида "labelLeft+labelRight"
    this.pairStartTime       = 0;    // когда впервые появилась эта пара
    this.lastLoggedGesturePair = null; // чтобы залогировать пару только один раз
    // Для одиночных жестов
    this.lastSingleLabel      = null;
    this.singleStartTime      = 0;
    this.lastLoggedSingle     = null;
    // Для пары жестов
    this.currentPairLabel       = null;
    this.pairStartTime          = 0;
    this.lastLoggedGesturePair  = null;
    // Mapping gesture labels to Russian words (for display)
    this.gestureMap = {
      'Closed_Fist': 'кулак',
      'Open_Palm':   'ладонь',
      'Pointing_Up': 'указательный палец вверх',
      'Thumb_Up':    'большой палец вверх',
      'Thumb_Down':  'большой палец вниз',
      'Victory':     'жест "Victory"',       // V sign
      'ILoveYou':    'жест "Я люблю тебя"',   // ILY sign
      'OK':          'жест "OK"'           // кружок
    };

    // Initialize the application
    this.init();
  }

  // В методе init() добавить:
async init() {
  this.log('🚀 Инициализация системы...', 'info');
  this.setupEventListeners();
  await this.initCamera();
  await this.initGestureRecognition();
  this.log('🎯 Система готова к работе', 'success');
}

  

  setupEventListeners() {
    // Connect UI buttons to their handlers
    document.getElementById('toggleGestures').addEventListener('click', () => {
      this.toggleGestures();
    });
    document.getElementById('calibrateBtn').addEventListener('click', () => {
      this.calibrate();
    });
    // Slider controls for thresholds
    document.getElementById('gestureThreshold').addEventListener('input', (e) => {
      this.gestureThreshold = parseFloat(e.target.value);
      document.getElementById('gestureThresholdValue').textContent =
        Math.round(this.gestureThreshold * 100) + '%';
    });
    document.getElementById('confidenceThreshold').addEventListener('input', (e) => {
      this.confidenceThreshold = parseFloat(e.target.value);
      document.getElementById('confidenceThresholdValue').textContent =
        Math.round(this.confidenceThreshold * 100) + '%';
    });
    // В методе setupEventListeners() добавить:
    document.getElementById('clearLogBtn').addEventListener('click', () => {
      this.clearLog();
    });
  }

  async initCamera() {
    try {
      // Request access to the webcam
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: false
      });
      // Set the video element source to the webcam stream
      this.videoElement = document.getElementById('videoElement');
      this.videoElement.srcObject = stream;
      // Prepare the overlay canvas for drawing
      this.canvasElement = document.getElementById('gestureCanvas');
      this.canvasCtx = this.canvasElement.getContext('2d');
      // Получаем ссылку на заглушку
      this.placeholderImg = document.getElementById('placeholderImg');
      // По умолчанию: видео скрыто, заглушка видна
      this.videoElement.style.display   = 'none';
      this.canvasElement.style.display  = 'none';
      this.placeholderImg.style.display = 'block';
      // Resize canvas to match video resolution once metadata is loaded
      this.videoElement.onloadedmetadata = () => {
        this.canvasElement.width = this.videoElement.videoWidth;
        this.canvasElement.height = this.videoElement.videoHeight;
      };
      this.log('Камера инициализирована', 'success');
    } catch (error) {
      this.log('Ошибка доступа к камере: ' + error.message, 'error');
    }
  }

  async initGestureRecognition() {
    try {
      // Initialize MediaPipe GestureRecognizer with the default model
      const vision = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
      );
      this.gestureRecognizer = await GestureRecognizer.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task",
          delegate: "GPU"
        },
        runningMode: "VIDEO",  // live video mode
        numHands: 2          // expect at most one hand at a time
      });
      this.log('Распознавание жестов инициализировано', 'success');
    } catch (error) {
      this.log('Ошибка инициализации распознавания жестов: ' + error.message, 'error');
    }
  }

  // Begin processing video frames for gestures (called when gestures are toggled on)
  // Обновленный метод startGestureLoop с исправленной логикой gesture-label
  // Обновленный метод startGestureLoop с исправленной логикой gesture-label
async startGestureLoop() {
  if (!this.isGestureActive || !this.gestureRecognizer) return;
  const now = Date.now();

  // Всегда рендерим видео на canvas, чтобы не «замораживать» изображение
  this.canvasCtx.save();
  this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
  
  // Применяем зеркалирование для видео
  this.canvasCtx.scale(-1, 1);
  this.canvasCtx.translate(-this.canvasElement.width, 0);
  
  this.canvasCtx.drawImage(
    this.videoElement,
    0, 0,
    this.canvasElement.width,
    this.canvasElement.height
  );
  this.canvasCtx.restore();

  // Получаем распознавание
  const { gestures = [], landmarks = [] } = this.gestureRecognizer.recognizeForVideo(this.videoElement, now);

  const leftTextElem   = document.getElementById('gestureTextLeft');
  const rightTextElem  = document.getElementById('gestureTextRight');
  const leftConfElem   = document.getElementById('confidenceTextLeft');
  const rightConfElem  = document.getElementById('confidenceTextRight');
  const gestureTextElem = document.getElementById('gestureText'); // Элемент gesture-label

  // --- 0 рук: сброс UI и состояния ---
  if (landmarks.length === 0) {
    leftTextElem.textContent   = 'Левая: —';
    rightTextElem.textContent  = 'Правая: —';
    leftConfElem.textContent   = '—%';
    rightConfElem.textContent  = '—%';
    gestureTextElem.textContent = 'Жест: не распознан';

    this.lastSingleLabel       = null;
    this.lastLoggedSingle      = null;
    this.currentPairLabel      = null;
    this.lastLoggedGesturePair = null;

  // --- 1 рука: одиночный жест ---
  } else if (landmarks.length === 1) {
    const { categoryName: lbl, score } = gestures[0][0];
    
    // Проверяем, что жест не "None" (не распознан)
    if (lbl !== 'None') {
      const name = this.gestureMap[lbl] || lbl;

      // UI для gesture-feedback
      leftTextElem.textContent   = `Одна рука: ${name}`;
      rightTextElem.textContent  = 'Правая: —';
      leftConfElem.textContent   = `${Math.round(score * 100)}%`;
      rightConfElem.textContent  = '—%';
      
      // UI для gesture-label
      gestureTextElem.textContent = `Жест: ${name}`;

      // Логика одиночного жеста (2 сек удержания)
      if (lbl !== this.lastSingleLabel) {
        this.lastSingleLabel      = lbl;
        this.singleStartTime      = now;
        this.lastLoggedSingle     = null;
      } else if (!this.lastLoggedSingle && now - this.singleStartTime >= 2000) {
        this.log(`Жест: ${name}`, 'info');
        this.lastLoggedSingle = lbl;
      }
    } else {
      // Жест не распознан
      leftTextElem.textContent   = 'Одна рука: не распознан';
      rightTextElem.textContent  = 'Правая: —';
      leftConfElem.textContent   = '—%';
      rightConfElem.textContent  = '—%';
      gestureTextElem.textContent = 'Жест: не распознан';
      
      this.lastSingleLabel = null;
      this.lastLoggedSingle = null;
    }

    // Сбрасываем пару
    this.currentPairLabel      = null;
    this.lastLoggedGesturePair = null;

    // Рисуем эту руку
    this._drawSkeleton(landmarks);

  // --- ≥2 рук: парный жест ---
  } else {
    // Определяем левую/правую по x координате запястья
    // Поскольку видео теперь зеркалируется, меняем логику
    const x0 = landmarks[0][0].x, x1 = landmarks[1][0].x;
    const leftIdx  = x0 > x1 ? 0 : 1;  // Изменили с < на >
    const rightIdx = leftIdx === 0 ? 1 : 0;

    const gL = gestures[leftIdx][0], gR = gestures[rightIdx][0];
    const lblL = gL.categoryName, lblR = gR.categoryName;

    // Проверяем, что хотя бы один жест распознан
    if (lblL !== 'None' || lblR !== 'None') {
      const nameL = lblL !== 'None' ? (this.gestureMap[lblL] || lblL) : 'не распознан';
      const nameR = lblR !== 'None' ? (this.gestureMap[lblR] || lblR) : 'не распознан';

      // UI для gesture-feedback
      leftTextElem.textContent   = `Левая: ${nameL}`;
      rightTextElem.textContent  = `Правая: ${nameR}`;
      leftConfElem.textContent   = lblL !== 'None' ? `${Math.round(gL.score * 100)}%` : '—%';
      rightConfElem.textContent  = lblR !== 'None' ? `${Math.round(gR.score * 100)}%` : '—%';

      // UI для gesture-label - показываем информацию о двух руках
      gestureTextElem.textContent = `Левая рука: ${nameL} - Правая рука: ${nameR}`;
      
      // Логика пары (2 сек удержания) - только если оба жеста распознаны
      if (lblL !== 'None' && lblR !== 'None') {
        const pairLabel = `${lblL}+${lblR}`;
        if (pairLabel !== this.currentPairLabel) {
          this.currentPairLabel      = pairLabel;
          this.pairStartTime         = now;
          this.lastLoggedGesturePair = null;
        } else if (!this.lastLoggedGesturePair && now - this.pairStartTime >= 2000) {
          this.log(`Жесты: левая — ${nameL}; правая — ${nameR}`, 'info');
          this.lastLoggedGesturePair = pairLabel;
        }
      } else {
        // Сбрасываем логику пары если хотя бы один жест не распознан
        this.currentPairLabel = null;
        this.lastLoggedGesturePair = null;
      }
    } else {
      // Оба жеста не распознаны
      leftTextElem.textContent   = 'Левая: не распознан';
      rightTextElem.textContent  = 'Правая: не распознан';
      leftConfElem.textContent   = '—%';
      rightConfElem.textContent  = '—%';
      gestureTextElem.textContent = 'Жесты: не распознаны';
      
      this.currentPairLabel = null;
      this.lastLoggedGesturePair = null;
    }

    // Сбрасываем одиночный жест
    this.lastSingleLabel = null;
    this.lastLoggedSingle = null;

    // Рисуем обе руки
    this._drawSkeleton(landmarks);
  }

  // Запускаем следующий кадр
  requestAnimationFrame(() => this.startGestureLoop());
}


  processGestureResult(gestureLabel, score, allLandmarks) {
    const now = Date.now();
    // Check if the same gesture was seen recently (within 1s)
    if (gestureLabel === this.lastGesture && now - this.lastGestureTime < 1000) {
      this.gestureStabilityCount += 1;
    } else {
      this.gestureStabilityCount = 1;
    }
    this.lastGesture = gestureLabel;
    this.lastGestureTime = now;

    // If the gesture persisted for 3+ frames and confidence is high enough, treat as stable
    if (this.gestureStabilityCount >= 3 && score >= this.gestureThreshold) {
      this.handleStableGesture(gestureLabel, score);
    }

    // Update HUD text with the detected gesture (mapped to a friendly name if possible)
    const displayName = this.gestureMap[gestureLabel] || gestureLabel;
    document.getElementById('gestureText').textContent = `Жест: ${displayName}`;
    document.getElementById('confidenceText').textContent = `Уверенность: ${Math.round(score * 100)}%`;

    // Draw landmarks on the canvas for feedback
    if (allLandmarks && this.canvasCtx) {
      this.canvasCtx.save();
      this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
      // Draw the current video frame onto the canvas as background
      this.canvasCtx.drawImage(this.videoElement, 0, 0, this.canvasElement.width, this.canvasElement.height);
      // Draw hand landmarks and connections
      const drawingUtils = new DrawingUtils(this.canvasCtx);
      for (const landmarks of allLandmarks) {
        drawingUtils.drawConnectors(landmarks, GestureRecognizer.HAND_CONNECTIONS,
                                    { color: '#00FF00', lineWidth: 4 });
        drawingUtils.drawLandmarks(landmarks, { color: '#FF0000', lineWidth: 2 });
      }
      this.canvasCtx.restore();
    }
  }

  handleStableGesture(gestureLabel, confidence) {
    // Log stable gesture detection
    this.log(`Стабильный жест: ${gestureLabel} (${Math.round(confidence * 100)}%)`, 'info');
    // (If voice command confirmation were active, we would handle thumbs-up/down here.
    // In gesture-only mode, no further action is required on stable gesture.)
  }

  // Toggle gesture recognition on/off
  toggleGestures() {
    this.isGestureActive = !this.isGestureActive;
    const btn = document.getElementById('toggleGestures');
    if (this.isGestureActive) {
      btn.textContent = '🤚 Остановить';
      btn.classList.add('active');
      // показываем видео, прячем заглушку
      this.placeholderImg.style.display = 'none';
      this.videoElement.style.display   = 'block';
      this.canvasElement.style.display  = 'block';
      this.videoElement.play();         // вдруг было на паузе
      this.log('Распознавание жестов включено', 'info');
      // Start analyzing video frames for gestures
      this.startGestureLoop();
    } else {
      btn.textContent = '🤚 Жесты';
      btn.classList.remove('active');
    // показываем заглушку, прячем видео + canvas
      this.placeholderImg.style.display = 'block';
      this.videoElement.style.display   = 'none';
      this.canvasElement.style.display  = 'none';
      this.videoElement.pause();
      this.log('Распознавание жестов выключено', 'info');
      // (The gesture loop will exit on the next frame automatically)
    }
  }

  calibrate() {
    // Dummy calibration sequence (simulated)
    this.log('Запуск калибровки...', 'info');
    this.updateStatus('processing', 'Калибровка...');
    setTimeout(() => {
      this.log('Калибровка завершена', 'success');
      this.updateStatus('active', 'Система готова');
    }, 2000);
  }

  // Изменить метод updateStatus():
  updateStatus(status, text) {
    const indicator = document.getElementById('statusIndicator');
    const statusTextElem = document.getElementById('statusText');
  
    indicator.className = `status-indicator status-${status}`;
    statusTextElem.textContent = text;
  
  // Обновляем также команды
    const commandDisplay = document.getElementById('commandDisplay');
    const commandText = commandDisplay.querySelector('.command-text');
  
    if (status === 'processing') {
      commandText.textContent = 'Обработка команды...';
    } else if (status === 'active') {
      commandText.textContent = 'Ожидание жестов...';
    } else if (status === 'listening') {
      commandText.textContent = 'Слушаю команды...';
    }
}

  // В методе log() добавить иконки:
log(message, type = 'info') {
  const logContainer = document.getElementById('logContainer');
  const entry = document.createElement('div');
  entry.className = `log-entry log-${type}`;
  
  let icon = '';
  switch(type) {
    case 'info': icon = 'ℹ️'; break;
    case 'success': icon = '✅'; break;
    case 'warning': icon = '⚠️'; break;
    case 'error': icon = '❌'; break;
  }
  
  entry.innerHTML = `
    <span class="log-icon">${icon}</span>
    <span class="log-time">[${new Date().toLocaleTimeString()}]</span>
    <span class="log-message">${message}</span>
  `;
  
  logContainer.insertBefore(entry, logContainer.firstChild);
  
  // Автоматическая очистка если записей больше 50
  if (logContainer.children.length > 50) {
    logContainer.removeChild(logContainer.lastChild);
  }
}

  _drawSkeleton(allLandmarks) {
  this.canvasCtx.save();
  this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
  
  // Применяем зеркалирование
  this.canvasCtx.scale(-1, 1);
  this.canvasCtx.translate(-this.canvasElement.width, 0);
  
  // Рисуем видео
  this.canvasCtx.drawImage(
    this.videoElement,
    0, 0,
    this.canvasElement.width,
    this.canvasElement.height
  );
  
  // Создаем новый контекст для рисования landmark'ов без зеркалирования
  this.canvasCtx.restore();
  this.canvasCtx.save();
  
  const drawer = new DrawingUtils(this.canvasCtx);
  
  // Рисуем максимум первые две руки
  allLandmarks.slice(0, 2).forEach(landmarks => {
    // Зеркалируем координаты landmark'ов
    const mirroredLandmarks = landmarks.map(landmark => ({
      x: 1 - landmark.x,  // инвертируем x координату
      y: landmark.y,
      z: landmark.z
    }));
    
    drawer.drawConnectors(
      mirroredLandmarks,
      GestureRecognizer.HAND_CONNECTIONS,
      { color: '#ffffff', lineWidth: 4 }
    );
    drawer.drawLandmarks(
      mirroredLandmarks,
      { color: '#b388eb', lineWidth: 2 }
    );
  });
  
  this.canvasCtx.restore();
}

clearLog() {
  const logContainer = document.getElementById('logContainer');
  logContainer.innerHTML = '';
  this.log('Журнал событий очищен', 'info');
}
}

// Initialize the app once the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new MonitorControlSPA();
});
