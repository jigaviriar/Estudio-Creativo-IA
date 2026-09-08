import auth


def test_designer_can_generate_but_not_approve(monkeypatch):
    monkeypatch.setattr(auth, "current_user", lambda: ("Test", "Diseñador"))
    assert auth.can("generar_imagen")
    assert not auth.can("aprobar")
    assert not auth.can("editar_contenido")


def test_redactor_can_edit_but_not_approve(monkeypatch):
    monkeypatch.setattr(auth, "current_user", lambda: ("Test", "Redactor"))
    assert auth.can("editar_contenido")
    assert not auth.can("aprobar")
    assert not auth.can("generar_imagen")


def test_only_approver_can_approve(monkeypatch):
    monkeypatch.setattr(auth, "current_user", lambda: ("Test", "Aprobador"))
    assert auth.can("aprobar")
    assert not auth.can("generar_imagen")
    assert not auth.can("editar_contenido")
