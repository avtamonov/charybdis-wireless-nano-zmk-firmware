"""Standard US-key-position to Russian-host-layout legends for the Base layer."""

BASE_LATIN = tuple("QWERTYUIOPASDFGHJKL;ZXCVBNM,./")
BASE_RUSSIAN = tuple("йцукенгшщзфывапролджячсмитьбю.")

assert len(BASE_LATIN) == len(BASE_RUSSIAN) == 30
