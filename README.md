# INVENTOR FW10010040-V1

## Monitoring Agent

The [Monitoring Agent](src/agent/) is a core component of our network monitoring system, designed to execute a range of diagnostic and performance assessments across network infrastructures. Each agent is a robust, stand-alone module capable of running independently across various segments of the network, from edge devices to central servers. These agents actively gather data on network health, efficiency, and security, transmitting this information back to central management systems for analysis and response.

Monitoring agents are equipped with the tools to perform both scheduled and on-demand tests, ensuring comprehensive coverage and immediate responsiveness to emerging issues. They are capable of:
* Automatically detecting network events or anomalies.
* Collecting and forwarding detailed logs and metrics for centralized analysis.
* Updating their configurations from a central repository to adapt to new testing requirements or network changes.

Agents are designed to be lightweight and easily deployable on a variety of hardware and network environments, including virtual machines, dedicated hardware, and cloud platforms. The deployment process is streamlined to support rapid scaling, allowing network administrators to swiftly increase monitoring capabilities in response to expanding network infrastructure or escalating demand.

## Monitoring Test Cases

This project is dedicated to the development of a comprehensive system for active network monitoring through the use of targeted tests. Utilizing agents distributed throughout the network, the system performs a range of tests from simple connectivity assessments, such as ping, to more sophisticated synthetic transactions. These tests are crucial for evaluating network performance, reliability, and overall health.
At the core of our monitoring strategy is a structured approach to test execution and data collection. Each test is meticulously configured via detailed JSON documents, which outline general execution parameters and specific configurations for individual tests. This ensures that each monitoring agent deployed across various network segments operates according to precise guidelines.
A pivotal aspect of the system’s design is its flexibility and scalability. This adaptability allows for the easy integration of new test types and the system’s expansion to accommodate growing network infrastructures. As networks evolve and new technologies are adopted, the monitoring system can seamlessly adjust, continuing to provide critical insights into network performance and security.
This repository houses a comprehensive collection of test cases across various categories. Each category is tailored to address specific network functions and potential issues, ensuring that all aspects of the network’s performance and security are monitored. Comprehensive documentation accompanies each test case, providing users with the information necessary to understand, deploy, and leverage these tests effectively within their own networks.

## Test Case Specifications

The following test case specifications are used to implement the test cases.
| Test Name | Category | Test Description |
|------|----------|-------------------------------|
| [network.ping](src/network/network.ping/) | Network | A PING test verifies the reachability of a host on an IP network by measuring the round-trip time for messages sent from the originating host to a destination computer. Essential for assessing network connectivity and performance. |
| [network.traceroute](src/network/network.traceroute/) | Network | This test traces the path that packets take from the source to a specified destination across a network, identifying each hop to diagnose potential issues in the network path.  |
| [network.dns](src/network/network.dns/) | Network | Designed to verify DNS service functionality by resolving specified DNS names or a list of predefined entries, ensuring DNS reliability and performance.  |
| [network.smtp](src/network/network.smtp/) | Network | Tests the capability of SMTP servers to send emails effectively, verifying the server's ability to handle outgoing emails without errors.  |
| [network.imap](src/network/network.imap/) | Network | Evaluates the functionality of IMAP servers to retrieve emails, essential for ensuring the reliability of email communication.  |
| [network.mqtt](src/network/network.mqtt/) | Network | Tests the MQTT protocol used for lightweight messaging in publish/subscribe systems, crucial for IoT communications. |
| [network.ntp](src/network/network.ntp/) | Network | Ensures that the Network Time Protocol (NTP) is functioning correctly for time synchronization across computer systems.  |
| [network.snmp](src/network/network.snmp/) | Network | Actively monitors SNMP-managed devices for key performance metrics such as CPU usage and network traffic, critical for network management.  |
| [network.ftp](src/network/network.ftp/) | Network | Tests FTP services for file transfers between clients and servers, ensuring that files can be sent and received reliably over the network. |
| [HTTP](src/webapp/webapp.http/) | Webapp | Evaluates the Hypertext Transfer Protocol for its effectiveness in facilitating communication between web servers and clients. |
| [performance.bandwidth](src/performance/performance.bandwidth/) | Performance | Measures network performance metrics such as jitter, latency, packet loss, and throughput, essential for network quality assessment.  |
| [security.ssh](src/security/security.ssh/) | Security | Tests the SSH protocol for securely managing network services over unsecured networks, ensuring the encryption and security of data in transit.  |
| [SSL/TLS](src/security/security.tls/) | Security | Validates the implementation of SSL/TLS protocols for securing connections between networked computers, critical for protecting data integrity and privacy. |
| [Web Security](src/webapp/webapp.security/) | Webapp | Tests the security settings the HTTPS endpoint. |
| [REST API](src/webapp/webapp.rest/) | Webapp | Tests RESTful APIs for correct responses and structure, focusing on JSON object analysis to ensure API reliability and compliance with specifications. |
| [SQL DB (PostgreSQL, MSSQL, MySQL)](/src/other/other.sql/) | Other | Evaluates database operations for SQL databases like PostgreSQL, MSSQL, and MySQL, ensuring database performance and data integrity. |
| [No SQL databases](src/other/other.nosql/) | Other | Tests operations for selected NoSQL databases, assessing their performance and scalability under various data loads. |
| [security.ldap](src/security/security.ldap/) | Security | Tests LDAP protocol implementations for managing and accessing distributed directory information services, ensuring that directory operations are performed efficiently and securely. |

# License

## BSD-3-Clause License

This project is licensed under the BSD-3-Clause License, which grants broad permission to use, modify, and distribute the software, provided that the following conditions are met:

1. **Redistributions of source code** must retain the above copyright notice, this list of conditions, and the following disclaimer.
   
2. **Redistributions in binary form** must reproduce the above copyright notice, this list of conditions, and the following disclaimer in the documentation and/or other materials provided with the distribution.
   
3. **Neither the name of Flowmon Networks, Brno University of Technology nor the names of its contributors** may be used to endorse or promote products derived from this software without specific prior written permission.

This license does not require you to release the source code of any modifications you make to the software, but it does not permit proprietary licensing, meaning any derivative work must also be licensed under BSD-3.

## Copyright

© 2025 Flowmon Networks and Brno University of Technology. All rights reserved.

This copyright notice pertains to all the software, documentation, and other materials included in this repository, unless otherwise stated.

## Contributors

The following developers have contributed to this project:

Martin Holkovič, Martin Elich, Jan Pikl, Pavel Podlužanský, Radek Friedl, Michal Pánek, Dias Assatulla, Pavel Horáček, Kristián Kičinka, Václav Korvas, Petr Matoušek, Nelson Mutua, Marko Poľanský, Libor Polčák, Ondřej Ryšavý
