import sys
import re


def import_file(lines):
    tags_label = "TAGS: "
    separator = 60*"-"

    idx = 0
    while idx < len(lines):
        assert lines[idx].startswith(tags_label)
        tags = lines[idx][len(tags_label):].split(",")
        tags = [t.strip() for t in tags if t.strip()]

        idx += 1

        body = []

        while idx < len(lines) and not lines[idx].startswith(separator):
            body.append(lines[idx])
            idx += 1

        idx += 1  # skip separator

        import pypandoc

        body = "\n".join(body)

        body = pypandoc.convert(body, "org", format="markdown_phpextra")

        if tags:
            lineend = body.find("\n")
            if lineend == -1:
                lineend = len(body)

            tags_str = " " + ":%s:" % (":".join(tags))

            body = body[:lineend] + tags_str + body[lineend:]

        body = "** " + re.sub(r"^\*+ ", "", body)

        print(body)


def main():
    with open(sys.argv[1], "r") as inf:
        lines = list(inf)

    import_file(lines)


if __name__ == "__main__":
    main()
