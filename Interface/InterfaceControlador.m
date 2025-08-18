s = serial('COM3', 'BaudRate', 115200); % Substitua 'COM3' pela porta correta
fopen(s);
data = fscanf(s); % Lê os dados enviados pelo Python
fclose(s);
delete(s);
clear s;