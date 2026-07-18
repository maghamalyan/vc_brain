import vc_brain
import vc_brain.dashboard
import vc_brain.eval
import vc_brain.features
import vc_brain.ingest
import vc_brain.labels
import vc_brain.memo
import vc_brain.models


def test_package_imports() -> None:
    modules = (
        vc_brain,
        vc_brain.dashboard,
        vc_brain.eval,
        vc_brain.features,
        vc_brain.ingest,
        vc_brain.labels,
        vc_brain.memo,
        vc_brain.models,
    )

    assert all(module.__name__.startswith("vc_brain") for module in modules)
    assert len(modules) == 8

