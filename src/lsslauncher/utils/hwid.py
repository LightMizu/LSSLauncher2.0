import hashlib
import platform
import subprocess

def get_hwid(salt: str = '') -> str:
    """
    Возвращает кроссплатформенный уникальный идентификатор машины (HWID)
    """
    
    uuid_str = None
    if platform.system() == "Windows":
        import wmi
        
        try:
            uuid_str = wmi.WMI().Win32_ComputerSystemProduct()[0].UUID
        except:
            pass
        if not uuid_str:
            try:
                command = 'powershell -Command "(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID"'  # noqa: E501
                output = subprocess.check_output(command, shell=True, text=True)
                uuid_str = output.strip()
            except:
                pass
    else:
        # На Linux/Mac можно использовать disk UUID
        try:
            if platform.system() == "Linux":
                output = subprocess.check_output("blkid -o value -s UUID $(df / | tail -1 | awk '{print $1}')", shell=True)
                uuid_str = output.decode().strip()
            elif platform.system() == "Darwin":
                output = subprocess.check_output("ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID", shell=True)
                uuid_str = output.decode().split('=')[1].strip().strip('"')
        except:
            pass
    if not uuid_str:
        uuid_str = "example"
    # Хешируем все данные, чтобы получить короткий HWID
    hwid = hashlib.sha256(uuid_str.encode()).hexdigest()
    return hwid