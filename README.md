# Demeter

Demeter is an Arduino & Raspberry Pi-based hydroponics robot.

![](./docs/demeter-splash.png)

Presently, it tracks:
- water level high 
- water level low
- water pH 
- water temperature
- water TDS
- volume of distilled/RO water dispensed
- volume of pH buffer dispensed

-and controls:
- a 5v magnetic stirrer for pH buffer solution administration
- a 12v peristaltic  pump for pH buffer solution administration
- a 12v peristaltic  pump for distilled/RO water auto-top-off
- a 12v submerged pump for reservoir circulation

-while logging to:
- redis
- AdaFruit.IO

The Arduino side is C and the Raspberry Pi side is Python 3. Tested on a 13 year old peace lilly.




