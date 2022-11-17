def read_file(filename, lines: object = None, file=None):
    if lines is None:
        lines = []
    try:
        file = open(filename, "r")
        return file.readlines()
    except Exception as e:
        print("ERROR reading file ", filename, e)
        return lines
    finally:
        if file is not None:
            file.close()
            print(filename, " closed")


print(read_file("C:/ansi.txt"))
print(read_file("C:/no.txt", "File Not Exists"))
print(read_file("C:/unicode.txt"))
