/*
  Digit transition effects. They act on the four hour/minute tubes only -
  the two seconds tubes step once a second and are deliberately left alone.
*/
void flipTick() {
  if (FLIP_EFFECT == 0) {
    sendHM(hrs, mins);
    newTimeFlag = false;
  }

  // ---- crossfade ----
  else if (FLIP_EFFECT == 1) {
    if (!flipInit) {
      flipInit = true;
      for (byte i = 0; i < NUM_HM; i++)
        flipIndics[i] = (indiDigits[i] != newTime[i]);
    }
    if (flipTimer.isReady()) {
      if (!indiBrightDirection) {
        indiBrightCounter--;
        if (indiBrightCounter <= 0) {
          indiBrightDirection = true;
          indiBrightCounter = 0;
          sendHM(hrs, mins);
        }
      } else {
        indiBrightCounter++;
        if (indiBrightCounter >= indiMaxBright) {
          indiBrightDirection = false;
          indiBrightCounter = indiMaxBright;
          flipInit = false;
          newTimeFlag = false;
        }
      }
      for (byte i = 0; i < NUM_HM; i++)
        if (flipIndics[i]) indiDimm[i] = indiBrightCounter;
    }
  }

  // ---- count up through the digits ----
  else if (FLIP_EFFECT == 2) {
    if (!flipInit) {
      flipInit = true;
      for (byte i = 0; i < NUM_HM; i++)
        flipIndics[i] = (indiDigits[i] != newTime[i]);
    }
    if (flipTimer.isReady()) {
      byte flipCounter = 0;
      for (byte i = 0; i < NUM_HM; i++) {
        if (flipIndics[i]) {
          indiDigits[i]--;
          if (indiDigits[i] < 0) indiDigits[i] = 9;
          if (indiDigits[i] == newTime[i]) flipIndics[i] = false;
        } else flipCounter++;
      }
      if (flipCounter == NUM_HM) {
        flipInit = false;
        newTimeFlag = false;
      }
    }
  }

  // ---- scroll along the physical cathode stack ----
  else if (FLIP_EFFECT == 3) {
    if (!flipInit) {
      flipInit = true;
      for (byte i = 0; i < NUM_HM; i++) {
        if (indiDigits[i] != newTime[i]) {
          flipIndics[i] = true;
          for (byte c = 0; c < 10; c++) {
            if (cathodeMask[c] == indiDigits[i]) startCathode[i] = c;
            if (cathodeMask[c] == newTime[i]) endCathode[i] = c;
          }
        } else flipIndics[i] = false;
      }
    }
    if (flipTimer.isReady()) {
      byte flipCounter = 0;
      for (byte i = 0; i < NUM_HM; i++) {
        if (flipIndics[i]) {
          if (startCathode[i] > endCathode[i]) {
            startCathode[i]--;
            indiDigits[i] = cathodeMask[startCathode[i]];
          } else if (startCathode[i] < endCathode[i]) {
            startCathode[i]++;
            indiDigits[i] = cathodeMask[startCathode[i]];
          } else flipIndics[i] = false;
        } else flipCounter++;
      }
      if (flipCounter == NUM_HM) {
        flipInit = false;
        newTimeFlag = false;
      }
    }
  }

  // ---- train ----
  else if (FLIP_EFFECT == 4) {
    if (!flipInit) {
      flipInit = true;
      currentLamp = 0;
      trainLeaving = true;
      flipTimer.reset();
    }
    if (flipTimer.isReady()) {
      if (trainLeaving) {
        for (byte i = 3; i > currentLamp; i--) indiDigits[i] = indiDigits[i - 1];
        anodeStates[currentLamp] = 0;
        currentLamp++;
        if (currentLamp >= NUM_HM) {
          trainLeaving = false;
          currentLamp = 0;
        }
      } else {
        for (byte i = currentLamp; i > 0; i--) indiDigits[i] = indiDigits[i - 1];
        indiDigits[0] = newTime[3 - currentLamp];
        anodeStates[currentLamp] = 1;
        currentLamp++;
        if (currentLamp >= NUM_HM) {
          flipInit = false;
          newTimeFlag = false;
        }
      }
    }
  }

  // ---- elastic band ----
  else if (FLIP_EFFECT == 5) {
    if (!flipInit) {
      flipInit = true;
      flipEffectStages = 0;
      flipTimer.reset();
    }
    if (flipTimer.isReady()) {
      switch (flipEffectStages++) {
        case 1:  anodeStates[3] = 0; break;
        case 2:  anodeStates[2] = 0; indiDigits[3] = indiDigits[2]; anodeStates[3] = 1; break;
        case 3:  anodeStates[3] = 0; break;
        case 4:  anodeStates[1] = 0; indiDigits[2] = indiDigits[1]; anodeStates[2] = 1; break;
        case 5:  anodeStates[2] = 0; indiDigits[3] = indiDigits[1]; anodeStates[3] = 1; break;
        case 6:  anodeStates[3] = 0; break;
        case 7:  anodeStates[0] = 0; indiDigits[1] = indiDigits[0]; anodeStates[1] = 1; break;
        case 8:  anodeStates[1] = 0; indiDigits[2] = indiDigits[0]; anodeStates[2] = 1; break;
        case 9:  anodeStates[2] = 0; indiDigits[3] = indiDigits[0]; anodeStates[3] = 1; break;
        case 10: anodeStates[3] = 0; break;
        case 11: indiDigits[0] = newTime[3]; anodeStates[0] = 1; break;
        case 12: anodeStates[0] = 0; indiDigits[1] = newTime[3]; anodeStates[1] = 1; break;
        case 13: anodeStates[1] = 0; indiDigits[2] = newTime[3]; anodeStates[2] = 1; break;
        case 14: anodeStates[2] = 0; indiDigits[3] = newTime[3]; anodeStates[3] = 1; break;
        case 15: indiDigits[0] = newTime[2]; anodeStates[0] = 1; break;
        case 16: anodeStates[0] = 0; indiDigits[1] = newTime[2]; anodeStates[1] = 1; break;
        case 17: anodeStates[1] = 0; indiDigits[2] = newTime[2]; anodeStates[2] = 1; break;
        case 18: indiDigits[0] = newTime[1]; anodeStates[0] = 1; break;
        case 19: anodeStates[0] = 0; indiDigits[1] = newTime[1]; anodeStates[1] = 1; break;
        case 20: indiDigits[0] = newTime[0]; anodeStates[0] = 1; break;
        case 21: flipInit = false; newTimeFlag = false; break;
      }
    }
  }
}
