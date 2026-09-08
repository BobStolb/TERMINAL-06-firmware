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
      newTimeFlag = true;   // BUGFIX: without this the tubes keep showing
                            // whatever was displayed before this correction
                            // (e.g. a bad boot-time RTC read) until the next
                            // secs>59 rollover happens to also fire - up to
                            // a minute of stale/nonsense digits. Inherited
                            // as-is from AlexGyver's original timeTicker.ino.
    }
    if (newTimeFlag) setNewTime();

    // seconds tubes step immediately, every second, with no effect applied
    if (curMode == 0) sendSeconds(secs);
  }
}
