
![HYKU logo long](https://user-images.githubusercontent.com/18311413/151296349-7dda3d0f-50e5-45e4-92ab-da6190cb1612.png)


Status: Under development

## Idea

![HYKU Comparison Table](https://user-images.githubusercontent.com/18311413/151644011-40247c3f-1858-4fe7-b977-91bd842aceee.png "enter image title here")


The idea behind the LLT is an pointing device for playing osu! that combines the absolute position sensing of a drawing tablet with the low latency and high polling rate of a mouse.


Please note that the colors and materials of the product are subject to change.



## Configuration Utility
![configurator screenshot](https://user-images.githubusercontent.com/18311413/151927797-098c77c6-c0cf-4f20-8955-63f58b2a89a5.png)

The HYKU tablet is plug and play and requires no drivers. The screen and tablet area settings are configured and saved on the tablet through the HYKU Configurator utility.

The configurator utility exposes:
- Setting Screen area and Tablet area
- Setting smoothing

## FAQ

**What is the polling rate and latency of the tablet?**

The polling rate is 550 Hz. The internal filtering is kept to a minimum to provide a worst case latency of 1.8ms. The end-to-end latency (pen input to monitor output) is subject to external factors like the game FPS, monitor refresh rate and latency, etc.

**What is the maximum tablet area?**

Approximately 100mm x 80mm.

**What is the maximum resolution of the tablet?**

Due to geometry, the resolution of the tablet increases as the pen moves closer to the center joint of the tablet. At maximum distance, the spatial resolution is 0.168mm, while at minimum distance, the spatial resolution is  0.091mm.

** What is the advantage of higher polling rates?

Higher polling rates don't just offer better reaction times, it also provides more accurate tracking of fast movements. See image below for an example:

![enter image description here](https://user-images.githubusercontent.com/18311413/147843408-313765c4-39ae-4b70-8b45-a95333d086ce.png "enter image title here")

# HYKU Tablet - CAD

![comparison table](https://user-images.githubusercontent.com/18311413/151644011-40247c3f-1858-4fe7-b977-91bd842aceee.png)


This repo contains 3D CAD and PCB CAD Files

![TBL2](https://user-images.githubusercontent.com/18311413/151928230-37d69286-3b1a-4be6-8ce3-51baddb28af4.png)


![output_2021-12-25](https://user-images.githubusercontent.com/18311413/147380542-2b0fd6ac-12e6-4994-9144-c370a167ab2c.png)
