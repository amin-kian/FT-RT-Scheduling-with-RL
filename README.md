# Analysing Energy Consumption When Tolerating Faults in Two Real-Time Fault Tolerant Scheduling Algorithms on Heterogeneous Systems

FEST and EnSuRe are two fault tolerant scheduling algorithms for real-time heterogeneous multicore systems that has two types of processors: one or more low-power (LP) cores, and one high-performance (HP) core. They both use a backup overloading strategy with the goal of minimising the energy consumption of the system.

## Requirements

Python 3.8

## Setup

Clone this repository.

```
git clone [https://github.com/amin-kian/FT-RT-Scheduling-with-RL]
```

The required Python libraries can be installed using pip via requirements.txt.
```
cd FT-RT-Scheduling-with-RL
pip install -r ./requirements.txt
```

## How to Run

Navigate to this directory. Then, launch Jupyter Notebook:
```
jupyter notebook
```

Open "FEST and EnSuRe Simulation.ipynb" and run the cells in order.

## References

[1]	P. P. Nair, R. Devaraj and A. Sarkar, "FEST:    Fault-Tolerant Energy-Aware Scheduling on Two-Core Heterogeneous Platform," 2018 8th International Symposium on Embedded Computing and System Design (ISED), 2018, pp. 63-68, doi: 10.1109/ISED.2018.8704123.

[2]	S. Saha et al., "EnSuRe: Energy & Accuracy Aware Fault-tolerant Scheduling on Real-time Heterogeneous Systems," 2021 IEEE 27th International Symposium on On-Line Testing and Robust System Design (IOLTS), 2021, pp. 1-4, doi: 10.1109/IOLTS52814.2021.9486707.
