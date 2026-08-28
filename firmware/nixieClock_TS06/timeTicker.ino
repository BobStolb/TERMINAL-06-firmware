byte minsCount = 0;

void calculateTime() {
  dotFlag = !dotFlag;
  if (dotFlag) {
    dotBrightFlag = true;
    dotBrightDirection = true;
    dotBrightCounter = 0;
    secs++;
    if (secs > 59) {
      newTimeFlag = true;
      secs = 0;
      mins++;
      minsCount++;

      if (minsCount >= 15) {              // resync with the RTC every 15 min
        minsCount = 0;
        DateTime now = rtc.now();
        secs = now.second();
        mins = now.minute();
        hrs  = now.hour();
      }

      if (mins % BURN_PERIOD == 0) burnIndicators();
    }
    if (mins > 59) {
      mins = 0;
      hrs++;
      if (hrs > 23) hrs = 0;
      changeBright();
    }
    if (newTimeFlag) setNewTime();

    // seconds tubes step immediately, every second, with no effect applied
    if (curMode == 0) sendSeconds(secs);
  }
}
