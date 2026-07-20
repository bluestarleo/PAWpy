"""PAWpy quickstart — the common workflows end to end.

Run against a real PAW instance by filling in the connection details below.
The UI URL-builder calls (``paw.ui.*`` / ``*.get_embed_url``) make no network
request, so they work even without a live server.
"""

from PAWpy import PAWService


def main():
    with PAWService(
        host="paw.mycompany.com",
        auth_mode="oauth",
        client_id="my-client-id",
        client_secret="my-client-secret",
        token_url="https://idp.mycompany.com/oauth2/token",
        scope="paw",
        database="Planning Sample",   # default TM1 database for paw.tm1()
        verify=True,
    ) as paw:

        # --- Content: list books in a folder -------------------------------
        for book in paw.books.get_all("/shared/Finance"):
            print(book.name, "->", paw.books.get_embed_url(book.path))

        # --- Content: generic asset CRUD -----------------------------------
        folder = paw.content.create_folder(name="Reports 2026", path="/shared/Finance")
        print("created folder id:", folder.id)

        # --- Admin: registered TM1 servers ---------------------------------
        for server in paw.admin.get_tm1_servers():
            print("server:", server.get("name"))

        # --- TM1 proxy: run MDX through PAW --------------------------------
        tm1 = paw.tm1("Planning Sample")
        print("cubes:", [c.get("Name") for c in tm1.get_cubes()][:5])
        cellset = tm1.execute_mdx(
            "SELECT {[Account].[Revenue]} ON 0 FROM [Revenue Cube]"
        )
        print("cells returned:", len(cellset.get("Cells", [])))

        # --- UI: pure embed-URL builders (no HTTP) -------------------------
        print(paw.ui.book_url("/shared/Finance/Monthly Report", embed=True))
        print(paw.ui.cube_viewer_url("Planning Sample", "plan_BudgetPlan", view="Budget Input"))
        print(paw.ui.dimension_editor_url("Planning Sample", "plan_business_unit"))


if __name__ == "__main__":
    main()
