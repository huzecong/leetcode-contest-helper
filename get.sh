if [[ $1 == "--debug" ]]; then
    shift
    python main.py --debug get -l cpp -l python -p contest $@
else
    python main.py get -l cpp -l python -p contest $@
fi
