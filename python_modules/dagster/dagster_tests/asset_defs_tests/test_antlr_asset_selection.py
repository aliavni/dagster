import dagster as dg
import pytest
from dagster._core.definitions.antlr_asset_selection.antlr_asset_selection import (
    AntlrAssetSelectionParser,
    KeyWildCardAssetSelection,
)
from dagster._core.definitions.antlr_asset_selection.generated.AssetSelectionParser import (
    AssetSelectionParser,
)
from dagster._core.definitions.asset_selection import (
    AssetSelection,
    ChangedInBranchAssetSelection,
    CodeLocationAssetSelection,
    ColumnAssetSelection,
    ColumnTagAssetSelection,
    StatusAssetSelection,
    TableNameAssetSelection,
)


@pytest.mark.parametrize(
    "selection_str, expected_tree_str",
    [
        ("*", "(start (expr *) <EOF>)"),
        (
            "key:a",
            "(start (expr (traversalAllowedExpr (attributeExpr key : (keyValue a)))) <EOF>)",
        ),
        (
            'key:"*/a+"',
            '(start (expr (traversalAllowedExpr (attributeExpr key : (keyValue "*/a+")))) <EOF>)',
        ),
        (
            "sinks(key:a)",
            "(start (expr (traversalAllowedExpr (functionName sinks) ( (expr (traversalAllowedExpr (attributeExpr key : (keyValue a)))) ))) <EOF>)",
        ),
        (
            "roots(key:a)",
            "(start (expr (traversalAllowedExpr (functionName roots) ( (expr (traversalAllowedExpr (attributeExpr key : (keyValue a)))) ))) <EOF>)",
        ),
        (
            "tag:foo=bar",
            "(start (expr (traversalAllowedExpr (attributeExpr tag : (value foo) = (value bar)))) <EOF>)",
        ),
        (
            'owner:"owner@owner.com"',
            '(start (expr (traversalAllowedExpr (attributeExpr owner : (value "owner@owner.com")))) <EOF>)',
        ),
        (
            "owner:<null>",
            "(start (expr (traversalAllowedExpr (attributeExpr owner : (value <null>)))) <EOF>)",
        ),
        (
            'group:"my_group"',
            '(start (expr (traversalAllowedExpr (attributeExpr group : (value "my_group")))) <EOF>)',
        ),
        (
            "kind:my_kind",
            "(start (expr (traversalAllowedExpr (attributeExpr kind : (value my_kind)))) <EOF>)",
        ),
        (
            "code_location:my_location",
            "(start (expr (traversalAllowedExpr (attributeExpr code_location : (value my_location)))) <EOF>)",
        ),
        (
            "(((key:a)))",
            "(start (expr (traversalAllowedExpr ( (expr (traversalAllowedExpr ( (expr (traversalAllowedExpr ( (expr (traversalAllowedExpr (attributeExpr key : (keyValue a)))) ))) ))) ))) <EOF>)",
        ),
        (
            "not key:a",
            "(start (expr not (expr (traversalAllowedExpr (attributeExpr key : (keyValue a))))) <EOF>)",
        ),
        (
            "key:a and key:b",
            "(start (expr (expr (traversalAllowedExpr (attributeExpr key : (keyValue a)))) and (expr (traversalAllowedExpr (attributeExpr key : (keyValue b))))) <EOF>)",
        ),
        (
            "key:a or key:b",
            "(start (expr (expr (traversalAllowedExpr (attributeExpr key : (keyValue a)))) or (expr (traversalAllowedExpr (attributeExpr key : (keyValue b))))) <EOF>)",
        ),
    ],
)
def test_antlr_tree(selection_str, expected_tree_str) -> None:
    asset_selection = AntlrAssetSelectionParser(selection_str, include_sources=True)
    assert asset_selection.tree_str == expected_tree_str

    generated_selection = asset_selection.asset_selection

    # Ensure the generated selection can be converted back to a selection string, and then back to the same selection
    regenerated_selection = AntlrAssetSelectionParser(
        generated_selection.to_selection_str(),
        include_sources=True,
    ).asset_selection
    assert regenerated_selection == generated_selection


@pytest.mark.parametrize(
    "selection_str",
    [
        "+",
        "*+",
        "**key:a",
        "not",
        "key:a key:b",
        "key:a and and",
        "key:a and",
        "sinks",
        "owner",
        "tag:foo=",
        "owner:owner@owner.com",
        "owner:<none>",
        "key:<fake>",
    ],
)
def test_antlr_tree_invalid(selection_str):
    with pytest.raises(Exception):
        AntlrAssetSelectionParser(selection_str)


@pytest.mark.parametrize(
    "selection_str, expected_assets",
    [
        ("key:a", KeyWildCardAssetSelection(selected_key_wildcard="a")),
        ('key:"*/a+"', KeyWildCardAssetSelection(selected_key_wildcard="*/a+")),
        ("key:prefix/thing", KeyWildCardAssetSelection(selected_key_wildcard="prefix/thing")),
        (
            "not key:a",
            AssetSelection.all(include_sources=True)
            - KeyWildCardAssetSelection(selected_key_wildcard="a"),
        ),
        (
            "NOT key:a",
            AssetSelection.all(include_sources=True)
            - KeyWildCardAssetSelection(selected_key_wildcard="a"),
        ),
        (
            "key:a and key:b",
            KeyWildCardAssetSelection(selected_key_wildcard="a")
            & KeyWildCardAssetSelection(selected_key_wildcard="b"),
        ),
        (
            "key:a AND key:b",
            KeyWildCardAssetSelection(selected_key_wildcard="a")
            & KeyWildCardAssetSelection(selected_key_wildcard="b"),
        ),
        (
            "key:a or key:b",
            KeyWildCardAssetSelection(selected_key_wildcard="a")
            | KeyWildCardAssetSelection(selected_key_wildcard="b"),
        ),
        (
            "key:a OR key:b",
            KeyWildCardAssetSelection(selected_key_wildcard="a")
            | KeyWildCardAssetSelection(selected_key_wildcard="b"),
        ),
        ("1+key:a", KeyWildCardAssetSelection(selected_key_wildcard="a").upstream(1)),
        ("2+key:a", KeyWildCardAssetSelection(selected_key_wildcard="a").upstream(2)),
        ("key:a+1", KeyWildCardAssetSelection(selected_key_wildcard="a").downstream(1)),
        ("key:a+2", KeyWildCardAssetSelection(selected_key_wildcard="a").downstream(2)),
        (
            "1+key:a+1",
            KeyWildCardAssetSelection(selected_key_wildcard="a").upstream(1)
            | KeyWildCardAssetSelection(selected_key_wildcard="a").downstream(1),
        ),
        ("+key:a", KeyWildCardAssetSelection(selected_key_wildcard="a").upstream()),
        ("key:a+", KeyWildCardAssetSelection(selected_key_wildcard="a").downstream()),
        (
            "+key:a+",
            KeyWildCardAssetSelection(selected_key_wildcard="a").downstream()
            | KeyWildCardAssetSelection(selected_key_wildcard="a").upstream(),
        ),
        (
            "key:a+ and +key:b",
            KeyWildCardAssetSelection(selected_key_wildcard="a").downstream()
            & KeyWildCardAssetSelection(selected_key_wildcard="b").upstream(),
        ),
        (
            "+key:a and key:b+ and +key:c+",
            KeyWildCardAssetSelection(selected_key_wildcard="a").upstream()
            & KeyWildCardAssetSelection(selected_key_wildcard="b").downstream()
            & (
                KeyWildCardAssetSelection(selected_key_wildcard="c").upstream()
                | KeyWildCardAssetSelection(selected_key_wildcard="c").downstream()
            ),
        ),
        ("sinks(key:a)", KeyWildCardAssetSelection(selected_key_wildcard="a").sinks()),
        ("roots(key:c)", KeyWildCardAssetSelection(selected_key_wildcard="c").roots()),
        ("tag:foo", AssetSelection.tag("foo", "", include_sources=True)),
        ("tag:foo=bar", AssetSelection.tag("foo", "bar", include_sources=True)),
        ('owner:"owner@owner.com"', AssetSelection.owner("owner@owner.com")),
        ("group:my_group", AssetSelection.groups("my_group", include_sources=True)),
        (
            "kind:my_kind",
            AssetSelection.kind("my_kind", include_sources=True),
        ),
        (
            "code_location:my_location",
            CodeLocationAssetSelection(selected_code_location="my_location"),
        ),
        ("status:healthy", StatusAssetSelection(selected_status="healthy")),
        ("column:my_column", ColumnAssetSelection(selected_column="my_column")),
        ("table_name:my_table", TableNameAssetSelection(selected_table_name="my_table")),
        ("column_tag:my_key=my_value", ColumnTagAssetSelection(key="my_key", value="my_value")),
        ("changed_in_branch:any", ChangedInBranchAssetSelection(selected_changed_in_branch="any")),
        ('tag:"<null>"', AssetSelection.tag("<null>", "", include_sources=True)),
        ('tag:""', AssetSelection.tag("", "", include_sources=True)),
        ('tag:"fake"=""', AssetSelection.tag("fake", "", include_sources=True)),
        ("owner:<null>", AssetSelection.owner(None)),
        ("group:<null>", AssetSelection.groups(include_sources=True)),
        (
            "kind:<null>",
            AssetSelection.kind(None, include_sources=True),
        ),
        (
            "code_location:<null>",
            CodeLocationAssetSelection(selected_code_location=None),
        ),
        ("column:<null>", ColumnAssetSelection(selected_column=None)),
        ("table_name:<null>", TableNameAssetSelection(selected_table_name=None)),
        ("column_tag:fake=<null>", ColumnTagAssetSelection(key="fake", value="")),
        (
            "changed_in_branch:<null>",
            ChangedInBranchAssetSelection(selected_changed_in_branch=None),
        ),
    ],
)
def test_antlr_visit_basic(selection_str, expected_assets) -> None:
    # a -> b -> c
    @dg.asset(tags={"foo": "bar"}, owners=["team:billing"])
    def a(): ...

    @dg.asset(deps=[a], kinds={"python", "snowflake"})
    def b(): ...

    @dg.asset(
        deps=[b],
        group_name="my_group",
    )
    def c(): ...

    generated_selection = AntlrAssetSelectionParser(
        selection_str, include_sources=True
    ).asset_selection
    assert generated_selection == expected_assets

    # Ensure the generated selection can be converted back to a selection string, and then back to the same selection
    regenerated_selection = AntlrAssetSelectionParser(
        generated_selection.to_selection_str(),
        include_sources=True,
    ).asset_selection
    assert regenerated_selection == expected_assets


def test_full_test_coverage() -> None:
    # Ensures that every Antlr literal is tested in test_antlr_visit_basic
    # by extension, also ensures that the to_selection_str method is tested
    # for all Antlr literals
    names = AssetSelectionParser.literalNames

    all_selection_strings_we_are_testing = [
        selection_str
        for selection_str, _ in test_antlr_visit_basic.pytestmark[0].args[1]  # pyright: ignore[reportFunctionMemberAccess]
    ]

    for name in names:
        if name in ("<INVALID>", "','"):
            continue

        name_substr = name.strip("'")
        assert any(
            name_substr in selection_str for selection_str in all_selection_strings_we_are_testing
        ), (
            f"Antlr literal {name_substr} is not under test in test_antlr_asset_selection.py:test_antlr_visit_basic"
        )
