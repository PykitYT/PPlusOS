program_name = "phttpserver"
class HTTPServer(Program):
    def main(self):
        def request_decode(data: str):
            firstline = data.splitlines()[0]
            version, method, path = firstline.split(maxsplit=2)
            body = '\n'.join(data.splitlines()[1:])
            return {
                "version": version,
                "method": method,
                "path": path,
                "body": body
            }
        def response_encode(version, int_code, str_code, body):
            return f"""{version} {int_code} {str_code}
        {body}"""

        io = self.io
        fs = self.syskernel.fs
        socket = self.syskernel.socket
        io.write('PhttpServer for PPlusOS\nEnter port: ')
        try:
            port = yield from io.read_line()
            port = int(port)
        except:
            io.write('Not an int.')
            return 1
        class HTTPServer_Background(Program):
            def main(self):
                nonlocal port
                io.write('Using folder /home/phttpserver/\n')
                if not fs.exists_folder('/home/phttpserver'):
                    io.write('Creating main page and folder.\n')
                    fs.create_folder('/home/phttpserver')
                    fs.open_file('/home/phttpserver/main.pg', 'w').write('Hello, pHTTP! Its running on PPlus!')
                sock = socket('server', port)
                while True:
                    cli = yield from sock.accept()
                    request = cli.read()
                    request = request_decode(request)
                    if request['path'] in ['/', ' ', '']:
                        request['path'] = '/main'
                    if request['version'] != 'phttp_pplus_r1':
                        cli.send(response_encode('phttp_pplus_r1', 500, 'Unsupported version', 'Unsupported version.'))
                        cli.close()
                        continue
                    path = '/home/phttpserver/' + request['path'] + '.pg'
                    if not fs.exists(path):
                        cli.send(response_encode('phttp_pplus_r1', 404, 'Not Found', 'Not found'))
                        cli.close()
                        continue
                    data = fs.open_file(path,'r').read()
                    cli.send(response_encode('phttp_pplus_r1', 200, 'OK', data ))
                    cli.close()
                    continue
        self.syskernel.create_process(HTTPServer_Background, False)
        return 0
