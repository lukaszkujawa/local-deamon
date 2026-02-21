from localdeamon.deamon import Deamon

def main():
    deamon = Deamon()

    task = """Research the impact of LLM coding on the software industry. """

    resp = deamon.run(task)
    print(resp)

if __name__ == '__main__':
    main()