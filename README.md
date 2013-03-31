bw_library
==========

Python library to talk to the BitWizard expansion boards on raspberry pi. 

This project is currently in "beta". 

Feel free to test it out, but please report any problems and suggestions. 


-----------------------------------------

This is the BitWizard API for the RPI or any Linux with /dev/spidevX.X 
or /dev/i2c-x devices

On raspberry pi you need to add: 
  i2c-dev
to the file /etc/modules to get the i2c-dev devices. (if you have an 
i2c-version of the boards)

Install:

	sudo python setup.py install

see examples dir for examples 

see doc for documentation

Have Fun!!


