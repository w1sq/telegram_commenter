Архитектура сервера:     /home -/python_parsers
	                         -/service
	                         -/manage_report



Директория для парсеров:  /home/python_parsers/   1) chastniye-zakazy
			    				        2) tendery
			    				        3) pobediteli-tenderov
			    			        	  4) others


Архитектура директории парсера на примере avito: /home/python_parsers/chastniye-zakazy/avito - директория парсера
Содержимое директории:					 1) avito_parser - директория где храниться сам парсер с виртуальным окружением(env)
								 2) avito.sh - скрипт запуска 
								 3) avito.log - отчет о работе



Директория с модулями для отправки собранных данных по api:     /home/manage_report/Send_report/Utils.py
Для того что бы импортировать уже отлаженный метод "send_to_api()" необходимо скопировать след. код : 	
															
															import sys
															import os
															currentdir = os.path.dirname(os.path.realpath(__file__))
															base_path = os.path.dirname(currentdir)
															sys.path.append(base_path)
															sys.path.append('/home/manage_report')
															from Send_report.Utils import send_to_api

Пример:													       
data = {'name': name_parser,
	  'data': list[dict]}										
send_to_api(data)
 
В случае если парсер упал с ошибкой, то метод send_to_api() не должен вызываться.
В случае если парсер успешно отработал, но актульных данных нет, то в метод send_to_api() передается словарь(см выше) {'name': name_parser,
																				'data': [] }


Директория для служебных файлов таких как chromedriver, firefox итд: /home/service