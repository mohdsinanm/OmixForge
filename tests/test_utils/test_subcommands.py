
from src.utils.subcommands.shell import *

def test_run_shell_command_success():

    result = run_shell_command("echo test")
    assert result.stdout == "test\n"
    assert result.returncode == 0
    assert result.stderr == ''

def test_run_shell_command_called_process_error():
    result = run_shell_command("badcmd")
    assert not result

def test_run_shell_command_stream_success():

    process, stream = run_shell_command_stream("""i=1
                            while [ $i -le 5 ]; do
                            echo "Line $i"
                            i=$((i+1))
                            done""")

    for i, v in enumerate(stream):
        assert v ==f"Line {i+1}"

def test_run_shell_command_stream_error():

    process, stream = run_shell_command_stream("""i=1
                            gibberish [ $i -le 5 ]; do
                            echo "Line $i"
                            i=$((i+1))
                            done""")

    assert "error" in process.stderr.read()




