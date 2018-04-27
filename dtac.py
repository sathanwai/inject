
######################################
#########__Injector Python__##########
######################################
#*Obs: so atende ao metodo CONNECT
#*Palavras-chave:
#[crlf] = \r\n
#[netData] = request line. Ex.: CONNECT a.com:443 HTTP/1.0
#[host] = host requisitado. Ex.: a.com
#[port] = porta requisitada. Ex.: 443
#[host_port] = conjuto host:port. Ex.: a.com:443
#[protocol] = protocol utilizado. Ex.: HTTP/1.0


###############__CONF__###############
BIND_ADDR = '127.0.0.1'
BIND_PORT = 8080
PROXT_ADDR = '10.4.4.4'
PROXY_PORT = 8080
PAYLOAD = 'CONNECT [host_port] [protocol][crlf]Host: static.line.naver.jp[crlf]X-Online-Host: static.line.naver.jp[crlf]Connection: Keep-Alive[crlf]User-Agent: Mozilla/5.0 (Linux; Android 7.1.1; SM-C710F Build/NMF26X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36[crlf][crlf]'


import socket
import thread
import string
import select

TAM_BUFFER = 1024
MAX_CLIENT_REQUEST_LENGTH = 1024 * 8

#Monta uma payload
def getReplacedPayload(payload, netData, hostPort, protocol):
	str = payload.replace('[netData]', netData)
	str = str.replace('[host_port]', (hostPort[0] + ':' + hostPort[1]))
	str = str.replace('[host]', hostPort[0])
	str = str.replace('[port]', hostPort[1])
	str = str.replace('[protocol]', protocol)
	str = str.replace('[crlf]', '\r\n')
	return str

#Separa o protocol HTTP de uma requisicao
def getRequestProtocol(request):
	inicio = request.find(' ', request.find(':')) + 1
	str = request[inicio:]
	fim = str.find('\r\n')
	
	return str[:fim]

#Separa o host e porta de uma requisicao
def getRequestHostPort(request):
	inicio = request.find(' ') + 1
	str = request[inicio:]
	fim = str.find(' ')
	
	hostPort = str[:fim]
	
	return hostPort.split(':')

#Separa a request line de uma requisicao
def getRequestNetData(request):
	return request[:request.find('\r\n')]

#Le uma request/response HTTP
def receiveHttpMsg(socket):
	len = 1
	
	data = socket.recv(1)
	while data.find('\r\n\r\n'.encode()) == -1:
		if not data: break
		data = data + socket.recv(1)
		len += 1
		if len > MAX_CLIENT_REQUEST_LENGTH: break
	
	return data
	
#Implementa o metodo CONNECT
def doConnect(clientSocket, serverSocket, tamBuffer):
	sockets = [clientSocket, serverSocket]
	timeout = 0
	print '<-> CONNECT started'
		
	while 1:
		timeout += 1
		ins, _, exs = select.select(sockets, [], sockets, 3)
		if exs: break
		
		if ins:
			for socket in ins:
				try:
					data = socket.recv(tamBuffer)
					if not data: break;
					
					if socket is serverSocket:
						clientSocket.sendall(data)
					else:
						serverSocket.sendall(data)

					timeout = 0
				except:
					break

		if timeout == 60: break
	
#Atente um cliente
def acceptThread(clientSocket, clientAddr):
	print '<-> Client connected: ', clientAddr
	
	#Le a requisicao cliente
	request = receiveHttpMsg(clientSocket)
	
	#Valida o metodo. Somente CONNECT e aceito
	if not request.startswith('CONNECT'):
		print '<!> Client requisitou metodo != CONNECT!'
		clientSocket.sendall('HTTP/1.1 405 Only_CONNECT_Method!\r\n\r\n')
		clientSocket.close()
		thread.exit()
	
	#Separa dados da request enviada
	netData = getRequestNetData(request)
	protocol = getRequestProtocol(request)
	hostPort = getRequestHostPort(netData)

	#Gera a requisicao final a partir da payload, com base nos dados da request enviada
	finalRequest = getReplacedPayload(PAYLOAD, netData, hostPort, protocol)
	
	#Envia a requisicao ao servidor proxy
	proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	proxySocket.connect((PROXT_ADDR, PROXY_PORT))
	proxySocket.sendall(finalRequest)
	
	#Recebe a resposta do servidor proxy
	proxyResponse = receiveHttpMsg(proxySocket)
	
	print '<-> Status line: ' + getRequestNetData(proxyResponse)
	
	#Envia a resposta do proxy ao cliente
	clientSocket.sendall(proxyResponse)
	
	#Se a resposta do proxy contem codigo 200, executa metodo CONNECT
	if proxyResponse.find('200 ') != -1:
		doConnect(clientSocket, proxySocket, TAM_BUFFER)
	
	#Fecha a conexao com o cliente
	print '<-> Client ended    : ', clientAddr
	proxySocket.close()
	clientSocket.close()
	thread.exit()

	
#############################__INICIO__########################################

print '\n'
print '==>Injector.py'
print '-->Listening   : ' + BIND_ADDR + ':' + str(BIND_PORT)
print '-->Remote proxy: ' + PROXT_ADDR + ':' + str(PROXY_PORT)
print '-->Payload     : ' + PAYLOAD
print '\n'

#Configura a escuta numa porta local
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((BIND_ADDR, BIND_PORT))
server.listen(1)

print '<-> Server listening... '

#Recebe o cliente e despacha uma thread para atende-lo
while True:
	clientSocket, clientAddr = server.accept()
	thread.start_new_thread(acceptThread, tuple([clientSocket, clientAddr]))

server.close()
