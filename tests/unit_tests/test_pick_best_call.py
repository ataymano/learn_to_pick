from typing import Any, Dict

import pytest
from test_utils import MockEncoder, MockEncoderReturnsList

import learn_to_pick
import learn_to_pick.base as rl_loop

encoded_keyword = "[encoded]"

class fake_llm_caller:
    def predict(self):
        return "hey"

class fake_llm_caller_with_score:
    def predict(self):
        return "3"

@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_multiple_ToSelectFrom_throws() -> None:
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    actions = ["0", "1", "2"]
    with pytest.raises(ValueError):
        pick.run(
            User=learn_to_pick.BasedOn("Context"),
            action=learn_to_pick.ToSelectFrom(actions),
            another_action=learn_to_pick.ToSelectFrom(actions),
        )


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_missing_basedOn_from_throws() -> None:
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    actions = ["0", "1", "2"]
    with pytest.raises(ValueError):
        pick.run(action=learn_to_pick.ToSelectFrom(actions))


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_ToSelectFrom_not_a_list_throws() -> None:
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    actions = {"actions": ["0", "1", "2"]}
    with pytest.raises(ValueError):
        pick.run(
            User=learn_to_pick.BasedOn("Context"),
            action=learn_to_pick.ToSelectFrom(actions),
        )


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_update_with_delayed_score_with_auto_validator_throws() -> None:
    auto_val_llm = fake_llm_caller_with_score
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        selection_scorer=learn_to_pick.AutoSelectionScorer(llm=auto_val_llm),
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    actions = ["0", "1", "2"]
    response = pick.run(
        User=learn_to_pick.BasedOn("Context"),
        action=learn_to_pick.ToSelectFrom(actions),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore

    assert picked_metadata.selected.score == 3.0  # type: ignore
    with pytest.raises(RuntimeError):
        pick.update_with_delayed_score(
            chain_response=response, score=100  # type: ignore
        )


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_update_with_delayed_score_force() -> None:
    # this LLM returns a number so that the auto validator will return that
    auto_val_llm = fake_llm_caller_with_score
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        selection_scorer=learn_to_pick.AutoSelectionScorer(llm=auto_val_llm),
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    actions = ["0", "1", "2"]
    response = pick.run(
        User=learn_to_pick.BasedOn("Context"),
        action=learn_to_pick.ToSelectFrom(actions),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score == 3.0  # type: ignore
    pick.update_with_delayed_score(
        chain_response=response, score=100, force_score=True  # type: ignore
    )
    assert picked_metadata.selected.score == 100.0  # type: ignore


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_update_with_delayed_score() -> None:
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        selection_scorer=None,
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    actions = ["0", "1", "2"]
    response = pick.run(
        User=learn_to_pick.BasedOn("Context"),
        action=learn_to_pick.ToSelectFrom(actions),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score is None  # type: ignore
    pick.update_with_delayed_score(chain_response=response, score=100)  # type: ignore
    assert picked_metadata.selected.score == 100.0  # type: ignore


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_user_defined_scorer() -> None:
    class CustomSelectionScorer(learn_to_pick.SelectionScorer):
        def score_response(
            self,
            inputs: Dict[str, Any],
            event: learn_to_pick.PickBestEvent,
        ) -> float:
            score = 200
            return score

    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        selection_scorer=CustomSelectionScorer(),
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    actions = ["0", "1", "2"]
    response = pick.run(
        User=learn_to_pick.BasedOn("Context"),
        action=learn_to_pick.ToSelectFrom(actions),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score == 200.0  # type: ignore


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_everything_embedded() -> None:
    feature_embedder = learn_to_pick.PickBestFeatureEmbedder(
        auto_embed=False, model=MockEncoder()
    )
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller, feature_embedder=feature_embedder, auto_embed=False
    )

    str1 = "0"
    str2 = "1"
    str3 = "2"
    encoded_str1 = rl_loop.stringify_embedding(list(encoded_keyword + str1))
    encoded_str2 = rl_loop.stringify_embedding(list(encoded_keyword + str2))
    encoded_str3 = rl_loop.stringify_embedding(list(encoded_keyword + str3))

    ctx_str_1 = "context1"

    encoded_ctx_str_1 = rl_loop.stringify_embedding(list(encoded_keyword + ctx_str_1))

    expected = f"""shared |User {ctx_str_1 + " " + encoded_ctx_str_1} \n|action {str1 + " " + encoded_str1} \n|action {str2 + " " + encoded_str2} \n|action {str3 + " " + encoded_str3} """  # noqa

    actions = [str1, str2, str3]

    response = pick.run(
        User=rl_loop.EmbedAndKeep(learn_to_pick.BasedOn(ctx_str_1)),
        action=rl_loop.EmbedAndKeep(learn_to_pick.ToSelectFrom(actions)),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    vw_str = feature_embedder.format(picked_metadata)  # type: ignore
    assert vw_str == expected


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_default_auto_embedder_is_off() -> None:
    feature_embedder = learn_to_pick.PickBestFeatureEmbedder(
        auto_embed=False, model=MockEncoder()
    )
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller, feature_embedder=feature_embedder
    )

    str1 = "0"
    str2 = "1"
    str3 = "2"
    ctx_str_1 = "context1"

    expected = f"""shared |User {ctx_str_1} \n|action {str1} \n|action {str2} \n|action {str3} """  # noqa

    actions = [str1, str2, str3]

    response = pick.run(
        User=learn_to_pick.base.BasedOn(ctx_str_1),
        action=learn_to_pick.base.ToSelectFrom(actions),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    vw_str = feature_embedder.format(picked_metadata)  # type: ignore
    assert vw_str == expected


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_default_w_embeddings_off() -> None:
    feature_embedder = learn_to_pick.PickBestFeatureEmbedder(
        auto_embed=False, model=MockEncoder()
    )
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller, feature_embedder=feature_embedder, auto_embed=False
    )

    str1 = "0"
    str2 = "1"
    str3 = "2"
    ctx_str_1 = "context1"

    expected = f"""shared |User {ctx_str_1} \n|action {str1} \n|action {str2} \n|action {str3} """  # noqa

    actions = [str1, str2, str3]

    response = pick.run(
        User=learn_to_pick.BasedOn(ctx_str_1),
        action=learn_to_pick.ToSelectFrom(actions),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    vw_str = feature_embedder.format(picked_metadata)  # type: ignore
    assert vw_str == expected


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_default_w_embeddings_on() -> None:
    feature_embedder = learn_to_pick.PickBestFeatureEmbedder(
        auto_embed=True, model=MockEncoderReturnsList()
    )
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller, feature_embedder=feature_embedder, auto_embed=True
    )

    str1 = "0"
    str2 = "1"
    ctx_str_1 = "context1"
    dot_prod = "dotprod 0:5.0"  # dot prod of [1.0, 2.0] and [1.0, 2.0]

    expected = f"""shared |User {ctx_str_1} |@ User={ctx_str_1}\n|action {str1} |# action={str1} |{dot_prod}\n|action {str2} |# action={str2} |{dot_prod}"""  # noqa

    actions = [str1, str2]

    response = pick.run(
        User=learn_to_pick.BasedOn(ctx_str_1),
        action=learn_to_pick.ToSelectFrom(actions),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    vw_str = feature_embedder.format(picked_metadata)  # type: ignore
    assert vw_str == expected


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_default_embeddings_mixed_w_explicit_user_embeddings() -> None:
    feature_embedder = learn_to_pick.PickBestFeatureEmbedder(
        auto_embed=True, model=MockEncoderReturnsList()
    )
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller, feature_embedder=feature_embedder, auto_embed=True
    )

    str1 = "0"
    str2 = "1"
    encoded_str2 = learn_to_pick.stringify_embedding([1.0, 2.0])
    ctx_str_1 = "context1"
    ctx_str_2 = "context2"
    encoded_ctx_str_1 = learn_to_pick.stringify_embedding([1.0, 2.0])
    dot_prod = "dotprod 0:5.0 1:5.0"  # dot prod of [1.0, 2.0] and [1.0, 2.0]

    expected = f"""shared |User {encoded_ctx_str_1} |@ User={encoded_ctx_str_1} |User2 {ctx_str_2} |@ User2={ctx_str_2}\n|action {str1} |# action={str1} |{dot_prod}\n|action {encoded_str2} |# action={encoded_str2} |{dot_prod}"""  # noqa

    actions = [str1, learn_to_pick.Embed(str2)]

    response = pick.run(
        User=learn_to_pick.BasedOn(learn_to_pick.Embed(ctx_str_1)),
        User2=learn_to_pick.BasedOn(ctx_str_2),
        action=learn_to_pick.ToSelectFrom(actions),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    vw_str = feature_embedder.format(picked_metadata)  # type: ignore
    assert vw_str == expected


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_default_no_scorer_specified() -> None:
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller_with_score,
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    response = pick.run(
        User=learn_to_pick.BasedOn("Context"),
        action=learn_to_pick.ToSelectFrom(["0", "1", "2"]),
    )
    # chain llm used for both basic prompt and for scoring
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score == 3.0  # type: ignore


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_explicitly_no_scorer() -> None:
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        selection_scorer=None,
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    response = pick.run(
        User=learn_to_pick.BasedOn("Context"),
        action=learn_to_pick.ToSelectFrom(["0", "1", "2"]),
    )
    # chain llm used for both basic prompt and for scoring
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score is None  # type: ignore


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_auto_scorer_with_user_defined_llm() -> None:
    scorer_llm = fake_llm_caller_with_score
    pick = learn_to_pick.PickBest.create(
        llm=fake_llm_caller,
        selection_scorer=learn_to_pick.AutoSelectionScorer(llm=scorer_llm),
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    response = pick.run(
        User=learn_to_pick.BasedOn("Context"),
        action=learn_to_pick.ToSelectFrom(["0", "1", "2"]),
    )
    # chain llm used for both basic prompt and for scoring
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score == 3  # type: ignore


@pytest.mark.requires("vowpal_wabbit_next", "sentence_transformers")
def test_activate_and_deactivate_scorer() -> None:
    llm = fake_llm_caller
    scorer_llm = fake_llm_caller_with_score
    pick = learn_to_pick.PickBest.create(
        llm=llm,
        selection_scorer=learn_to_pick.base.AutoSelectionScorer(llm=scorer_llm),
        feature_embedder=learn_to_pick.PickBestFeatureEmbedder(
            auto_embed=False, model=MockEncoder()
        ),
    )
    response = pick.run(
        User=learn_to_pick.base.BasedOn("Context"),
        action=learn_to_pick.base.ToSelectFrom(["0", "1", "2"]),
    )
    # chain llm used for both basic prompt and for scoring
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score == 3  # type: ignore

    pick.deactivate_selection_scorer()
    response = pick.run(
        User=learn_to_pick.base.BasedOn("Context"),
        action=learn_to_pick.base.ToSelectFrom(["0", "1", "2"]),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score is None  # type: ignore

    pick.activate_selection_scorer()
    response = pick.run(
        User=learn_to_pick.base.BasedOn("Context"),
        action=learn_to_pick.base.ToSelectFrom(["0", "1", "2"]),
    )
    picked_metadata = response["picked_metadata"]  # type: ignore
    assert picked_metadata.selected.score == 3  # type: ignore