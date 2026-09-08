// push hours, minutes and seconds onto the six tubes
void sendTime(byte hours, byte minutes, byte seconds) {
  indiDigits[0] = (byte)hours / 10;
  indiDigits[1] = (byte)hours % 10;

  indiDigits[2] = (byte)minutes / 10;
  indiDigits[3] = (byte)minutes % 10;

  indiDigits[4] = (byte)seconds / 10;
  indiDigits[5] = (byte)seconds % 10;
}

// hours+minutes only - used by the transition effects, which never touch
// the seconds tubes (they step once a second and would fight the effect)
void sendHM(byte hours, byte minutes) {
  indiDigits[0] = (byte)hours / 10;
  indiDigits[1] = (byte)hours % 10;
  indiDigits[2] = (byte)minutes / 10;
  indiDigits[3] = (byte)minutes % 10;
}

void sendSeconds(byte seconds) {
  indiDigits[4] = (byte)seconds / 10;
  indiDigits[5] = (byte)seconds % 10;
}

// target digits for the effects
void setNewTime() {
  newTime[0] = (byte)hrs / 10;
  newTime[1] = (byte)hrs % 10;
  newTime[2] = (byte)mins / 10;
  newTime[3] = (byte)mins % 10;
}
