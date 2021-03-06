EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
NoConn ~ 4800 3950
$Comp
L power:+3.3V #PWR02
U 1 1 61A543B3
P 3600 3600
F 0 "#PWR02" H 3600 3450 50  0001 C CNN
F 1 "+3.3V" H 3615 3773 50  0000 C CNN
F 2 "" H 3600 3600 50  0001 C CNN
F 3 "" H 3600 3600 50  0001 C CNN
	1    3600 3600
	1    0    0    -1  
$EndComp
Wire Wire Line
	3600 3950 3600 4050
$Comp
L power:GND #PWR01
U 1 1 61A5DC79
P 3600 4050
F 0 "#PWR01" H 3600 3800 50  0001 C CNN
F 1 "GND" H 3605 3877 50  0000 C CNN
F 2 "" H 3600 4050 50  0001 C CNN
F 3 "" H 3600 4050 50  0001 C CNN
	1    3600 4050
	1    0    0    -1  
$EndComp
Text GLabel 4800 3750 2    50   Input ~ 0
SCL
$Comp
L power:GND #PWR05
U 1 1 61A7900D
P 4950 3450
F 0 "#PWR05" H 4950 3200 50  0001 C CNN
F 1 "GND" H 4955 3277 50  0000 C CNN
F 2 "" H 4950 3450 50  0001 C CNN
F 3 "" H 4950 3450 50  0001 C CNN
	1    4950 3450
	1    0    0    -1  
$EndComp
Wire Wire Line
	4800 3650 4800 3450
Wire Wire Line
	4800 3450 4950 3450
$Comp
L Custom:AS5600 U1
U 1 1 61A40795
P 4400 3800
F 0 "U1" H 4400 4265 50  0000 C CNN
F 1 "AS5600" H 4400 4174 50  0000 C CNN
F 2 "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" H 4400 3800 50  0001 C CNN
F 3 "" H 4400 3800 50  0001 C CNN
	1    4400 3800
	1    0    0    -1  
$EndComp
Text GLabel 4800 3850 2    50   Input ~ 0
SDA2
Wire Wire Line
	3600 3950 4000 3950
$Comp
L Connector_Generic:Conn_01x05 J1
U 1 1 61A7262A
P 4450 2300
F 0 "J1" H 4368 1875 50  0000 C CNN
F 1 "Conn_01x05" H 4368 1966 50  0000 C CNN
F 2 "UltraLibrarian:SM05B-NSHSS-TBLFSN" H 4450 2300 50  0001 C CNN
F 3 "~" H 4450 2300 50  0001 C CNN
	1    4450 2300
	-1   0    0    1   
$EndComp
Text GLabel 4950 2300 2    50   Input ~ 0
SCL
Text GLabel 4950 2400 2    50   Input ~ 0
SDA2
$Comp
L power:+3.3V #PWR03
U 1 1 61A72633
P 4950 2100
F 0 "#PWR03" H 4950 1950 50  0001 C CNN
F 1 "+3.3V" H 4965 2273 50  0000 C CNN
F 2 "" H 4950 2100 50  0001 C CNN
F 3 "" H 4950 2100 50  0001 C CNN
	1    4950 2100
	1    0    0    -1  
$EndComp
Wire Wire Line
	4650 2100 4950 2100
$Comp
L power:GND #PWR04
U 1 1 61A7263A
P 5250 2500
F 0 "#PWR04" H 5250 2250 50  0001 C CNN
F 1 "GND" H 5255 2327 50  0000 C CNN
F 2 "" H 5250 2500 50  0001 C CNN
F 3 "" H 5250 2500 50  0001 C CNN
	1    5250 2500
	1    0    0    -1  
$EndComp
Wire Wire Line
	4650 2500 5250 2500
Wire Wire Line
	4650 2400 4950 2400
Wire Wire Line
	4950 2300 4650 2300
NoConn ~ 4000 3850
$Comp
L Device:C_Small C1
U 1 1 61BD5717
P 3600 3850
F 0 "C1" H 3692 3896 50  0000 L CNN
F 1 "100nF" H 3692 3805 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 3600 3850 50  0001 C CNN
F 3 "~" H 3600 3850 50  0001 C CNN
	1    3600 3850
	1    0    0    -1  
$EndComp
Connection ~ 3600 3950
Wire Wire Line
	3600 3600 3600 3650
Wire Wire Line
	4000 3650 3600 3650
Connection ~ 3600 3650
Wire Wire Line
	3600 3650 3600 3750
Wire Wire Line
	4000 3750 3600 3750
Connection ~ 3600 3750
Wire Wire Line
	4650 2200 5250 2200
Wire Wire Line
	5250 2200 5250 2500
Connection ~ 5250 2500
Entry Wire Line
	4350 4100 4450 4200
$EndSCHEMATC
