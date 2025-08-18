% Escolha o modo de comunicação: 'COM' ou 'TCP'
modo_comunicacao = 'COM';  

% Configuração da comunicação
if strcmp(modo_comunicacao, 'COM')
    porta_serial = 'COM3'; % Substitua pela porta correta
    baud_rate = 115200;
    dispositivo = serialport(porta_serial, baud_rate);
elseif strcmp(modo_comunicacao, 'TCP')
    endereco_ip = '192.168.0.112'; % Substitua pelo IP correto do ESP32
    porta_tcp = 12345; % Substitua pela porta correta
    dispositivo = tcpclient(endereco_ip, porta_tcp);
end

% Verifica se a conexão foi estabelecida
if isempty(dispositivo)
    error('Erro: O dispositivo não foi inicializado corretamente.');
end

% Inicializa variáveis para armazenamento
dados = [];

while true
    mensagem = ""; % Inicializa mensagem vazia
    
    if strcmp(modo_comunicacao, 'COM')
        if dispositivo.NumBytesAvailable > 0
            mensagem = char(read(dispositivo, dispositivo.NumBytesAvailable, "char")); % Leitura para `serialport`
        end
    elseif strcmp(modo_comunicacao, 'TCP')
        if dispositivo.BytesAvailable > 0
            mensagem = char(read(dispositivo, dispositivo.BytesAvailable, "char")); % Leitura para `tcpclient`
        end
    end
    
    % Verifica se uma mensagem válida foi recebida
    if ~isempty(mensagem)
        % Remove possíveis espaços em branco e caracteres indesejados
        mensagem = strtrim(mensagem);

        % Separa os dados assumindo que estão separados por espaço
        valores = str2double(strsplit(mensagem, ' '));

        % Ignora valores NaN e certifica que há 3 valores válidos
        if length(valores) == 3 && ~any(isnan(valores))
            dados = [dados; valores]; % Armazena os dados
            disp(valores); % Exibe os dados válidos recebidos
        end
    end
    
    % Aguarda um curto intervalo para evitar sobrecarga
    pause(0.1);
end