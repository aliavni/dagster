import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Union, cast

import dagster as dg
import pytest
from dagster import AssetKey
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
        CacheableAssetsDefinition,
    )

get_unique_asset_identifier = lambda a: (
    a.node_def.name if isinstance(a, dg.AssetsDefinition) else a.key
)


def check_asset_group(assets):
    for a in assets:
        if isinstance(a, dg.AssetsDefinition):
            asset_keys = a.keys
            for asset_key in asset_keys:
                assert a.group_names_by_key.get(asset_key) == "my_cool_group"
        elif isinstance(a, dg.SourceAsset):
            assert a.group_name == "my_cool_group"


def check_freshness_policy(assets, freshness_policy):
    for a in assets:
        if isinstance(a, dg.AssetsDefinition):
            asset_keys = a.keys
            for asset_key in asset_keys:
                assert a.legacy_freshness_policies_by_key.get(asset_key) == freshness_policy, (
                    asset_key
                )


def check_auto_materialize_policy(assets, auto_materialize_policy):
    for a in assets:
        if isinstance(a, dg.AssetsDefinition):
            asset_keys = a.keys
            for asset_key in asset_keys:
                assert (
                    a.auto_materialize_policies_by_key.get(asset_key) == auto_materialize_policy
                ), asset_key


def assert_assets_have_prefix(
    prefix: Union[str, Sequence[str]], assets: Sequence[dg.AssetsDefinition]
) -> None:
    for a in assets:
        if isinstance(a, dg.AssetsDefinition):
            asset_keys = a.keys
            for asset_key in asset_keys:
                observed_prefix = asset_key.path[:-1]
                if len(observed_prefix) == 1:
                    observed_prefix = observed_prefix[0]
                assert observed_prefix == prefix


def get_assets_def_with_key(
    assets: Sequence[Union[dg.AssetsDefinition, dg.SourceAsset]], key: AssetKey
) -> dg.AssetsDefinition:
    assets_by_key = {
        key: assets_def
        for assets_def in assets
        if isinstance(assets_def, dg.AssetsDefinition)
        for key in assets_def.keys
    }
    return assets_by_key[key]


def get_source_asset_with_key(
    assets: Sequence[Union[dg.AssetsDefinition, dg.SourceAsset]], key: AssetKey
) -> dg.SourceAsset:
    source_assets_by_key = {
        source_asset.key: source_asset
        for source_asset in assets
        if isinstance(source_asset, dg.SourceAsset)
    }
    return source_assets_by_key[key]


def test_load_assets_from_package_name():
    from dagster_tests.definitions_tests.module_loader_tests import asset_package

    assets_defs = dg.load_assets_from_package_name(asset_package.__name__)
    assert len(assets_defs) == 11

    assets_1 = [get_unique_asset_identifier(asset) for asset in assets_defs]

    assets_defs_2 = dg.load_assets_from_package_name(asset_package.__name__)
    assert len(assets_defs_2) == 11

    assets_2 = [get_unique_asset_identifier(asset) for asset in assets_defs]

    assert assets_1 == assets_2

    assets_3 = dg.load_assets_from_package_name(asset_package.__name__, include_specs=True)
    assert len(assets_3) == 13

    assert next(
        iter(
            a
            for a in assets_3
            if isinstance(a, dg.AssetSpec) and a.key == dg.AssetKey("top_level_spec")
        )
    )


def test_load_assets_from_package_module():
    from dagster_tests.definitions_tests.module_loader_tests import asset_package

    assets_1 = dg.load_assets_from_package_module(asset_package)
    assert len(assets_1) == 11

    assets_1 = [get_unique_asset_identifier(a) for a in assets_1]

    assets_2 = dg.load_assets_from_package_module(asset_package)
    assert len(assets_2) == 11

    assets_2 = [get_unique_asset_identifier(a) for a in assets_2]

    assert assets_1 == assets_2

    assets_3 = dg.load_assets_from_package_name(asset_package.__name__, include_specs=True)
    assert len(assets_3) == 13

    assert next(
        iter(
            a
            for a in assets_3
            if isinstance(a, dg.AssetSpec) and a.key == dg.AssetKey("top_level_spec")
        )
    )


def test_load_assets_from_modules(monkeypatch):
    from dagster_tests.definitions_tests.module_loader_tests import asset_package
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    collection_1 = dg.load_assets_from_modules([asset_package, module_with_assets])

    assets_1 = [get_unique_asset_identifier(a) for a in collection_1]

    collection_2 = dg.load_assets_from_modules([asset_package, module_with_assets])

    assets_2 = [get_unique_asset_identifier(a) for a in collection_2]

    assert assets_1 == assets_2

    with monkeypatch.context() as m:

        @dg.asset
        def little_richard():
            pass

        m.setattr(asset_package, "little_richard_dup", little_richard, raising=False)
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
            match=re.escape("Asset key little_richard is defined multiple times."),
        ):
            dg.load_assets_from_modules([asset_package, module_with_assets])

    # Create an AssetsDefinition with an identical spec to that in the module
    with monkeypatch.context() as m:

        @dg.asset
        def top_level_spec():
            pass

        m.setattr(asset_package, "top_level_spec_same_assets_def", top_level_spec, raising=False)
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
        ):
            dg.load_assets_from_modules([asset_package, module_with_assets], include_specs=True)

    # Create an asset spec with an identical key to a full fledged assetsdef. Won't cause an error unless include_specs=True
    with monkeypatch.context() as m:
        spec = dg.AssetSpec("chuck_berry")
        m.setattr(asset_package, "chuck_berry_spec", spec, raising=False)
        assets = dg.load_assets_from_modules([asset_package, module_with_assets])
        assert [get_unique_asset_identifier(a) for a in assets] == assets_1
        with pytest.raises(
            dg.DagsterInvalidDefinitionError,
        ):
            dg.load_assets_from_modules([asset_package, module_with_assets], include_specs=True)


@dg.asset(group_name="my_group")
def asset_in_current_module():
    pass


source_asset_in_current_module = dg.SourceAsset(dg.AssetKey("source_asset_in_current_module"))

spec_in_current_module = dg.AssetSpec("spec_in_current_module")


def test_load_assets_from_current_module():
    assets = dg.load_assets_from_current_module()
    assets = [get_unique_asset_identifier(a) for a in assets]
    assert set(assets) == {"asset_in_current_module", dg.AssetKey("source_asset_in_current_module")}
    assert len(assets) == 2
    assets = dg.load_assets_from_current_module(include_specs=True)
    assets = [get_unique_asset_identifier(a) for a in assets]
    assert len(assets) == 3
    assert set(assets) == {
        "asset_in_current_module",
        dg.AssetKey("source_asset_in_current_module"),
        dg.AssetKey("spec_in_current_module"),
    }


def test_load_assets_from_modules_with_group_name():
    from dagster_tests.definitions_tests.module_loader_tests import asset_package
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    assets = dg.load_assets_from_modules(
        [asset_package, module_with_assets], group_name="my_cool_group"
    )
    check_asset_group(assets)

    assets = dg.load_assets_from_package_module(asset_package, group_name="my_cool_group")
    check_asset_group(assets)


def test_respect_existing_groups():
    assets = dg.load_assets_from_current_module()
    assets_def = next(iter(a for a in assets if isinstance(a, dg.AssetsDefinition)))
    assert assets_def.group_names_by_key.get(dg.AssetKey("asset_in_current_module")) == "my_group"

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        dg.load_assets_from_current_module(group_name="yay")


def test_load_assets_with_freshness_policy():
    from dagster_tests.definitions_tests.module_loader_tests import asset_package
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    assets = dg.load_assets_from_modules(
        [asset_package, module_with_assets],
        legacy_freshness_policy=dg.LegacyFreshnessPolicy(maximum_lag_minutes=50),
    )
    check_freshness_policy(assets, dg.LegacyFreshnessPolicy(maximum_lag_minutes=50))

    assets = dg.load_assets_from_package_module(
        asset_package, legacy_freshness_policy=dg.LegacyFreshnessPolicy(maximum_lag_minutes=50)
    )
    check_freshness_policy(assets, dg.LegacyFreshnessPolicy(maximum_lag_minutes=50))


def test_load_assets_with_auto_materialize_policy():
    from dagster_tests.definitions_tests.module_loader_tests import asset_package
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    assets = dg.load_assets_from_modules(
        [asset_package, module_with_assets], auto_materialize_policy=AutoMaterializePolicy.eager()
    )
    check_auto_materialize_policy(assets, AutoMaterializePolicy.eager())

    assets = dg.load_assets_from_package_module(
        asset_package, auto_materialize_policy=AutoMaterializePolicy.lazy()
    )
    check_auto_materialize_policy(assets, AutoMaterializePolicy.lazy())


@pytest.mark.parametrize(
    "prefix",
    [
        "my_cool_prefix",
        ["foo", "my_cool_prefix"],
        ["foo", "bar", "baz", "my_cool_prefix"],
    ],
)
def test_prefix(prefix):
    from dagster_tests.definitions_tests.module_loader_tests import asset_package
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    assets = dg.load_assets_from_modules([asset_package, module_with_assets], key_prefix=prefix)
    assert_assets_have_prefix(prefix, assets)  # pyright: ignore[reportArgumentType]

    assets = dg.load_assets_from_package_module(asset_package, key_prefix=prefix)
    assert_assets_have_prefix(prefix, assets)  # pyright: ignore[reportArgumentType]


def _load_assets_from_module_with_assets(**kwargs):
    from dagster_tests.definitions_tests.module_loader_tests.asset_package import module_with_assets

    return dg.load_assets_from_modules([module_with_assets], **kwargs)


@pytest.mark.parametrize(
    "load_fn",
    [
        _load_assets_from_module_with_assets,
        lambda **kwargs: dg.load_assets_from_package_name(
            "dagster_tests.definitions_tests.module_loader_tests.asset_package", **kwargs
        ),
    ],
)
def test_source_key_prefix(load_fn):
    prefix = ["foo", "my_cool_prefix"]
    assets_without_prefix_sources = load_fn(key_prefix=prefix)
    assert get_source_asset_with_key(assets_without_prefix_sources, dg.AssetKey(["elvis_presley"]))
    assert get_assets_def_with_key(
        assets_without_prefix_sources, dg.AssetKey(["foo", "my_cool_prefix", "chuck_berry"])
    ).dependency_keys == {
        dg.AssetKey(["elvis_presley"]),
        dg.AssetKey(["foo", "my_cool_prefix", "miles_davis"]),
    }

    assets_with_prefix_sources = load_fn(
        key_prefix=prefix, source_key_prefix=["bar", "cooler_prefix"]
    )
    assert get_source_asset_with_key(
        assets_with_prefix_sources, dg.AssetKey(["bar", "cooler_prefix", "elvis_presley"])
    )
    assert get_assets_def_with_key(
        assets_with_prefix_sources, dg.AssetKey(["foo", "my_cool_prefix", "chuck_berry"])
    ).dependency_keys == {
        # source prefix
        dg.AssetKey(["bar", "cooler_prefix", "elvis_presley"]),
        # loadable prefix
        dg.AssetKey(["foo", "my_cool_prefix", "miles_davis"]),
    }

    assets_with_str_prefix_sources = load_fn(key_prefix=prefix, source_key_prefix="string_prefix")
    assert get_source_asset_with_key(
        assets_with_str_prefix_sources, dg.AssetKey(["string_prefix", "elvis_presley"])
    )


@pytest.mark.parametrize(
    "load_fn",
    [
        dg.load_assets_from_package_module,
        lambda x, **kwargs: dg.load_assets_from_package_name(x.__name__, **kwargs),
    ],
)
@pytest.mark.parametrize(
    "prefix",
    [
        "my_cool_prefix",
        ["foo", "my_cool_prefix"],
        ["foo", "bar", "baz", "my_cool_prefix"],
    ],
)
def test_load_assets_cacheable(load_fn, prefix):
    """Tests the load-from-module and load-from-package-name functinos with cacheable assets."""
    from dagster_tests.definitions_tests.module_loader_tests import asset_package_with_cacheable

    assets_defs = load_fn(asset_package_with_cacheable)
    assert len(assets_defs) == 3

    assets_defs = load_fn(asset_package_with_cacheable, group_name="my_cool_group")
    assert len(assets_defs) == 3

    for assets_def in assets_defs:
        cacheable_def = cast("CacheableAssetsDefinition", assets_def)
        resolved_asset_defs = cacheable_def.build_definitions(
            cacheable_def.compute_cacheable_data()
        )

        check_asset_group(resolved_asset_defs)

    assets_defs = load_fn(asset_package_with_cacheable, key_prefix=prefix)
    assert len(assets_defs) == 3

    for assets_def in assets_defs:
        cacheable_def = cast("CacheableAssetsDefinition", assets_def)
        resolved_asset_defs = cacheable_def.build_definitions(
            cacheable_def.compute_cacheable_data()
        )

        assert_assets_have_prefix(prefix, resolved_asset_defs)
