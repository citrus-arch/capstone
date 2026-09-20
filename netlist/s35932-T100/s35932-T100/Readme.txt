1.Home directory includes:

1.1 src
	---s35932_scan.v	for both Trojan inserted and free designs	

2.Trojan
Trojan Description
	The Trojan trigger is a comparator and gets activated only in the functional mode. After activation, the Trojan enables 
	the scan enable of a part of one scan chain in the functional mode and leaks the value of one internal signal through a test output pin.  

Trojan Taxonomy
	Insertion phase: Design
	Abstraction level: gate level 
	Activation mechanism: Internally conditionally triggered
	Effects: Change Functionality, Leak Information
	Location: Processor
	Physical characteristics: Functional