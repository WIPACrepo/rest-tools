# CHANGELOG



## v1.11.0 (2025-07-21)

### [minor]

* [minor] jwt integer times (#163)

* Add dynamic client registration example, mostly for token issuer.
* Remove `type` field from jwt by default.
* Add jwt option for integer times when creating tokens.

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`19ca071`](https://github.com/WIPACrepo/rest-tools/commit/19ca071a6c403adb283a5626592120209a29a727))


## v1.10.0 (2025-07-16)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`e913ad5`](https://github.com/WIPACrepo/rest-tools/commit/e913ad5b6da20eae7b4d9ef32469e0e8e6c8a67d))

### [minor]

* [minor] allow EC algorithms, and add more typing (#161)

Allow EllipticCurve cryptography, mostly in `utils.auth`.
Allow `store_tokens` to be awaitable.
Add more typing in several places to make pylance happy.

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`da30370`](https://github.com/WIPACrepo/rest-tools/commit/da3037023ee0efd6c16802a6d7d60f1c2140b352))


## v1.9.0 (2025-07-08)

### [minor]

* [minor] switch to using basic auth for client secret (#160)

Switch to using basic auth for client secret, as this is more in line
with the RFC and more secure.

Also bump the Python minimum version to 3.9.

---------

Co-authored-by: ric-evans &lt;emejqz@gmail.com&gt;
Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`1221028`](https://github.com/WIPACrepo/rest-tools/commit/1221028980bf1cadc504f5ee6647eae680fe7847))


## v1.8.7 (2025-04-15)

###  

* &lt;bot&gt; update dependencies*.log files(s) ([`43457c0`](https://github.com/WIPACrepo/rest-tools/commit/43457c0492df17e2cdfb2f073278db9702ceaeb8))

* Use `pypa/gh-action-pypi-publish@v1.12.4` ([`a781c6a`](https://github.com/WIPACrepo/rest-tools/commit/a781c6ab16fce6265ee6713b49070d2af39b0e73))


## v1.8.6 (2025-02-20)

###  

* Update GHA Workflow (Use `pyproject.toml`) (#158)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`11fdaa4`](https://github.com/WIPACrepo/rest-tools/commit/11fdaa4e85d3866d6de82802b2134f4591555cd6))


## v1.8.5 (2024-12-24)

###  

* Add patch retries (#157)

IceProd API requests use PATCH, and were failing with no retries. This
should allow these requests to retry.

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`4073684`](https://github.com/WIPACrepo/rest-tools/commit/40736841c1e4a5beeed306083533b2239bc20eba))


## v1.8.4 (2024-12-06)

###  

* `ArgumentHandler`: Support Custom Validation Errors (#156)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`b4b1210`](https://github.com/WIPACrepo/rest-tools/commit/b4b121034cc04d9ea326b5435b0ff718e7d953e7))


## v1.8.3 (2024-12-06)

###  

* Fix `ArgumentHandler`&#39;s `bool`-Parsing for JSON Arguments (#155)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`a9d0d72`](https://github.com/WIPACrepo/rest-tools/commit/a9d0d7224736dc945b5e3d09b4267efb49507ce6))


## v1.8.2 (2024-10-18)

###  

* Update the Server Loggers (#154) ([`ad011a4`](https://github.com/WIPACrepo/rest-tools/commit/ad011a434f72c547b7294834b3a5f9a194b3ea94))


## v1.8.1 (2024-10-18)

###  

* Turn Down Logging for Auth Failures (#153)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`29aebc7`](https://github.com/WIPACrepo/rest-tools/commit/29aebc77f36305d2f5cd682492adbfa1dbac3ae7))


## v1.8.0 (2024-10-09)

### [minor]

* Add Support for Python 3.13 [minor] (#152)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`241943d`](https://github.com/WIPACrepo/rest-tools/commit/241943d82224c9688f36d31a02c60d08b9ffadca))


## v1.7.9 (2024-09-12)

###  

* Add Top-Level Exports: `client`, `server`, `utils` (#151) ([`da2c730`](https://github.com/WIPACrepo/rest-tools/commit/da2c73088db4623ef1ef9e7672138b9f024aa4c8))


## v1.7.8 (2024-08-15)

###  

* add scopes and secret to device client example (#150)

* add scopes and secret

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`669ea3d`](https://github.com/WIPACrepo/rest-tools/commit/669ea3d7715708a98a51de42a4f45278ee00071b))


## v1.7.7 (2024-08-08)

###  

* add pkce to public device grants (#149)

* add pkce to public device grants

* &lt;bot&gt; update dependencies*.log files(s)

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`f8bc697`](https://github.com/WIPACrepo/rest-tools/commit/f8bc697022563ed63ca47a2613d179b989e74932))


## v1.7.6 (2024-06-27)

###  

* Add Ability to Provide `provider_info` to `OpenIDAuth` (#148)

* Add Ability to Provide `provider_info` to `OpenIDAuth`

* &lt;bot&gt; update dependencies*.log files(s)

* flake8

* mypy

* make `token_url` `&#34;&#34;` on default

* mypy (py 3.8)

* smaller diff

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`63f37d0`](https://github.com/WIPACrepo/rest-tools/commit/63f37d0ea8380832b0fe850244502e7b6f51fae9))


## v1.7.5 (2024-05-22)

###  

* Use openapi&#39;s `RequestsOpenAPIResponse` and Log on Error (#147)

* Use `openapi_core_requests.RequestsOpenAPIResponse` and Log on Error

* &lt;bot&gt; update dependencies*.log files(s)

* take 2

* better logging

* stable logging

* remove breakpoint

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`a0ce13a`](https://github.com/WIPACrepo/rest-tools/commit/a0ce13a4cc3af1fb0b64f60622f90d38a81d99f7))


## v1.7.4 (2024-05-03)

###  

* fix openid handler for newer keycloak (#146)

* fix openid handler for newer keycloak

* better default scope selection ([`33234ef`](https://github.com/WIPACrepo/rest-tools/commit/33234ef15586261915ba42123eb292f2aa3f2fa0))


## v1.7.3 (2024-05-01)

###  

* Accept User&#39;s Logger: `RestClient`-Derived Objects &amp; Factories (#144)

* Accept User&#39;s Logger: `ClientCredentialsAuth` &amp; `OpenIDRestClient`

* &lt;bot&gt; update dependencies*.log files(s)

* same for `DeviceGrantAuth` &amp; `SavedDeviceGrantAuth`

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`89c4bb8`](https://github.com/WIPACrepo/rest-tools/commit/89c4bb8b78e55f21a85a56e49b48a4582b0974ee))


## v1.7.2 (2024-04-22)

###  

* auth token leeway time (#142)

* add plumbing for configuring token time leeway, and set it to 1 minute by default

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`3e75757`](https://github.com/WIPACrepo/rest-tools/commit/3e75757d2f78d53072b1a8e916fe65285e3c9c3c))


## v1.7.1 (2024-04-15)

###  

* Remove Extra Logging (#141) ([`c409ca2`](https://github.com/WIPACrepo/rest-tools/commit/c409ca23b876f00c03198f78c492d1615478b91a))


## v1.7.0 (2024-04-15)

### [minor]

* Add OpenAPI Tools [minor] (#140)

* Add `validate_request` Decorator

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update dependencies*.log files(s)

* flake8

* mypy

* &lt;bot&gt; update dependencies*.log files(s)

* fix variable imports / hints

* add `client.utils.request_and_validate()`

* imports

* mypy (backward compat)

* pt 2

* add tests for `request_and_validate()`

* &lt;bot&gt; update dependencies*.log files(s)

* mypy

* update ci test yaml

* fix syntax error

* fix ci steps

* flake8

* limit telemetry tests

* fix url

* use callable for client fixture

* (test)

* use `pytest-asyncio`

* patch port

* pt 2

* trim fixture scope

* use `RestHandlerSetup`

* set debug

* misc attempts at getting this thing running

* use a `conftest.py`

* hmm

* (test)

* mypy

* (debug)

* its `RestHandler`

* add missing `async`

* move `TestHandler`

* (debug)

* &lt;bot&gt; update dependencies*.log files(s)

* pt 2

* pt 3

* async issue?

* use `asyncio.wrap_future`

* clean up

* clean up - 2

* clean up - 3

* fix response

* fix imports

* update httperror test

* (debug)

* assert error messages

* remove `assert 0`

* add `test_000__valid` to `validate_request_test.py`

* update test spec

* flake8

* fix indents

* str fix

* wrong url

* add complexity to test spec

* fix typo

* add invalid test cases

* pt 2

* fix no args allowed

* in openapi v3.1 to explicitly forbid extra query params

* no args allowed for post

* just use `rc.request()`

* pt 2

* asserting errors - 2

* pt 3

* pt 4

* pt 5

* pt 6

* pt 7

* pt 8

* pt 9

* pt 10

* pt 11

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`b1118f1`](https://github.com/WIPACrepo/rest-tools/commit/b1118f1644155a33b4b8361a5239090e8c8bf9c1))


## v1.6.1 (2024-03-06)

###  

* Replace &#34;root&#34; Logger Usage (#139)

* Replace &#34;root&#34; Logger Usage

* more

* revert doc format

* &lt;bot&gt; update dependencies*.log files(s)

* flake8

* use `LOGGER`

* and for `json_util.py`

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`3b6d49e`](https://github.com/WIPACrepo/rest-tools/commit/3b6d49e8eb783f69373512acf624fe76fe01468e))


## v1.6.0 (2023-10-11)

### [minor]

* Use `argparse` for Managing REST Arguments [minor] (#138)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`07153e0`](https://github.com/WIPACrepo/rest-tools/commit/07153e0e4cdfca11fffb5de11e23190d3891e7d2))


## v1.5.3 (2023-09-05)

###  

* Require `urllib3&gt;=2.0.4` (#137)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`bf0e5fc`](https://github.com/WIPACrepo/rest-tools/commit/bf0e5fcd1942c052ab1228e8f41ec863c8d8605d))


## v1.5.2 (2023-08-22)

###  

* Exponential Backoff Followup (#136)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`eae7160`](https://github.com/WIPACrepo/rest-tools/commit/eae7160f05f9bf5cdd9e9bffa1136baa0261ea3c))


## v1.5.1 (2023-08-08)

###  

* reduce logging noise (#134)

* reduce logging noise

* &lt;bot&gt; update dependencies*.log files(s)

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`f844ca0`](https://github.com/WIPACrepo/rest-tools/commit/f844ca0fec9d5e1873d5d3f95215508f26c98e14))


## v1.5.0 (2023-08-03)

### [minor]

* Auto-calculated Retries + Exponential Backoff Retries [minor] (#133) ([`bc3e56b`](https://github.com/WIPACrepo/rest-tools/commit/bc3e56b274938bd40e722dd1fdb1ed778aa201c8))


## v1.4.21 (2023-08-01)

###  

* CI Updates (#132)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`4908545`](https://github.com/WIPACrepo/rest-tools/commit/49085451b875024cc64016a52166f57d83ffbf9b))

* handle requests errors more gracefully (#130)

* handle requests errors more gracefully

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`caac493`](https://github.com/WIPACrepo/rest-tools/commit/caac4939643bb0f2a7c763d7f9e9f9243e3ae408))


## v1.4.20 (2023-05-30)

###  

* pyjwt 2.7.0 should work now, so change version lock (#127)

* pyjwt 2.7.0 should work now, so change version lock

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`0e710f4`](https://github.com/WIPACrepo/rest-tools/commit/0e710f49f849ad149f36d75bce612b34f99bdfee))


## v1.4.19 (2023-05-24)

###  

*  bump py-versions CI release v2.1 ([`c25c828`](https://github.com/WIPACrepo/rest-tools/commit/c25c828ecc3569a4654147768ab4d27b6a249da4))


## v1.4.18 (2023-04-05)

###  

* Fix WIPAC GHA Package Versions (#118)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`9fc5f8c`](https://github.com/WIPACrepo/rest-tools/commit/9fc5f8c8fd687ad50d4b9950d12796d286fffb5b))


## v1.4.17 (2023-04-04)

###  

* try refreshing saved token before skipping device code (#117)

* validate saved token before using it, mostly for an exp check

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* refresh tokens from keycloak don&#39;t have expiration, so try a full refresh

* fix flake8 and tests

* fix tests

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`1815de9`](https://github.com/WIPACrepo/rest-tools/commit/1815de9d816356d5c6acab4242115e4d51bc2ea3))


## v1.4.16 (2023-03-18)

###  

* Modify SavedDeviceGrantAuth to take timeout and retries (#116)

* DeviceGrantAuth and SavedDeviceGrantAuth now take timeout and retries arguments ([`fc59a2a`](https://github.com/WIPACrepo/rest-tools/commit/fc59a2a24c68b6f1089d4923d0e6f981607e72a1))


## v1.4.15 (2023-03-08)

###  

* add example clients (#113)

* add example clients

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* fix flake8

* clarify that we actually have functional RestClients, in case someone takes these examples as an application base

* fix flake8

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`4d0f368`](https://github.com/WIPACrepo/rest-tools/commit/4d0f368e0c72f3a30da49c65fae42cb7556dbcda))


## v1.4.14 (2023-03-02)

###  

* openid web handler token storage api (#112)

* provide an API for storing/retrieving token data, with the default being cookies

* fix tests and flake8

* mixins should come before base class to override if necessary

* allow refresh and user info to be None

* one more None possibility

* remove unnecessary except

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`5b74ba1`](https://github.com/WIPACrepo/rest-tools/commit/5b74ba1ea81d4dd132bf1a43af7b282267ab3f0e))


## v1.4.13 (2023-03-01)

###  

* add basic docs on oauth clients (#111)

* add basic docs on oauth clients

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* attempt to add links to the src

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`c49024b`](https://github.com/WIPACrepo/rest-tools/commit/c49024b91fd2835039ff4cc9beb9fe10725388e4))


## v1.4.12 (2023-02-17)

###  

* dependabot: bump WIPACrepo/wipac-dev-py-setup-action from 1.10 to 1.11 (#107)

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e009ec6`](https://github.com/WIPACrepo/rest-tools/commit/e009ec6ab1e280335128ac852801520daa514d96))


## v1.4.11 (2023-02-17)

###  

* CI Updates (#108)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`a2b4cf5`](https://github.com/WIPACrepo/rest-tools/commit/a2b4cf53327217e63e4acef57f50d792f4bd1706))


## v1.4.10 (2023-02-15)

###  

* work around previous .well-known discovery failures (#106) ([`517cb8f`](https://github.com/WIPACrepo/rest-tools/commit/517cb8fc7c88a55e62c4a42f0213c45ea9627064))


## v1.4.9 (2023-02-15)

###  

* allow OpenIDWebHandlerMixin to decode byte or str for the access token (#105)

* allow OpenIDWebHandlerMixin to decode bytes or strings for the access token

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* fix tests

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`63ae741`](https://github.com/WIPACrepo/rest-tools/commit/63ae741d95f386d8ca2bbb6fb70fa537e51000d1))


## v1.4.8 (2023-02-06)

###  

* add SavedDeviceGrantAuth (#103)

* add SavedDeviceGrantAuth

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* fix flake8

* fix bad token address

* fix update func

* convert to Path, and error out faster

* make mypy happy

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`ab8143f`](https://github.com/WIPACrepo/rest-tools/commit/ab8143f40766c99bb34b8dff07ea8c9da2373b4a))


## v1.4.7 (2023-02-03)

###  

* allow method to return non-awaitable in decorators (#102)

* allow method to return non-awaitable in decorators

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`c07dce5`](https://github.com/WIPACrepo/rest-tools/commit/c07dce5bfeb4ec8c54d5c61c7a3b67656b0af53e))


## v1.4.6 (2023-02-03)

###  

* add a handler mixin for openid auth user detection (#101)

* add a handler mixin for openid auth user detection

* fix flake8 ([`e7ac514`](https://github.com/WIPACrepo/rest-tools/commit/e7ac5148d914f5771a7d72858d69229075c00235))


## v1.4.5 (2023-02-01)

###  

* dependabot: bump WIPACrepo/wipac-dev-py-setup-action from 1.9 to 1.10 (#94)

Bumps [WIPACrepo/wipac-dev-py-setup-action](https://github.com/WIPACrepo/wipac-dev-py-setup-action) from 1.9 to 1.10.
- [Release notes](https://github.com/WIPACrepo/wipac-dev-py-setup-action/releases)
- [Commits](https://github.com/WIPACrepo/wipac-dev-py-setup-action/compare/v1.9...v1.10)

---
updated-dependencies:
- dependency-name: WIPACrepo/wipac-dev-py-setup-action
  dependency-type: direct:production
  update-type: version-update:semver-minor
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`955cc70`](https://github.com/WIPACrepo/rest-tools/commit/955cc700f336a82d041991381807811a423c748f))

* use offline token for client credentials (#100)

* use offline token.  elevate token function to public access

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

---------

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`70cadc1`](https://github.com/WIPACrepo/rest-tools/commit/70cadc191c56e46bbb537335f10dd6b220a44b87))


## v1.4.4 (2023-01-27)

###  

* Add regex matching for `choices` &amp; `forbiddens` (#99)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`c80b640`](https://github.com/WIPACrepo/rest-tools/commit/c80b640035c57204e697e5d8554e5164bded268a))


## v1.4.3 (2023-01-27)

###  

* `get_argument()`: Disallow `None` Values for Strings (#98)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`92d1126`](https://github.com/WIPACrepo/rest-tools/commit/92d1126308d6c9bf5ab4fb1f95158508cc95b0d3))


## v1.4.2 (2022-12-22)

###  

* mixin for setting Keycloak username in current_user (#93)

* add a mixin for getting the correct Keycloak username in the current_user attr

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-tests.txt

* fix flake8

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`74d22e7`](https://github.com/WIPACrepo/rest-tools/commit/74d22e7293e88e852796f8a36858f059ac499c28))


## v1.4.1 (2022-12-21)

###  

* forgot to add import for new decorator (#92) ([`3ba947f`](https://github.com/WIPACrepo/rest-tools/commit/3ba947fb1a4c11202f322b509efe60ce1aec6f0b))


## v1.4.0 (2022-12-21)

### [minor]

* [minor] add new decorator for flexible token attribute mapping (#91)

* add new decorator for flexible token attribute mapping

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-tests.txt

* fix codeql and flake8

* raise min py version to 3.8

* &lt;bot&gt; update setup.cfg

* pass along authorized roles downstream

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`535401d`](https://github.com/WIPACrepo/rest-tools/commit/535401d63c182b6461f49c1c6b0108f89231493c))


## v1.3.20 (2022-12-13)

###  

* Updates from SkyDriver (#90)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`f6973c6`](https://github.com/WIPACrepo/rest-tools/commit/f6973c68ac31b6395c4df443f30b889d67a4d1e1))


## v1.3.19 (2022-12-13)

###  

* restructure clients (#89)

* restructure clients.  separate out each client into its own file.  add device grant client.

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* add qrcode dependency

* &lt;bot&gt; update requirements-dev.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

* &lt;bot&gt; update requirements.txt

* fix mypy errors

* add basic tests

* resolve some codeql issues

* fix flake8 errors

* fix some mypy errors

* fix ordering so we have the logger variable ready

* more mypy fixes

* more mypy fixes 2

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`ad6455d`](https://github.com/WIPACrepo/rest-tools/commit/ad6455d51d6acaff4ce561bdd774720fe278293c))


## v1.3.18 (2022-12-12)

###  

* Add CodeQL workflow for GitHub code scanning (#82)

Co-authored-by: LGTM Migrator &lt;lgtm-migrator@users.noreply.github.com&gt; ([`5eb0c5e`](https://github.com/WIPACrepo/rest-tools/commit/5eb0c5ef0869b69661eaff6aedf09b287af940c6))


## v1.3.17 (2022-12-12)

###  

* dependabot: bump certifi from 2022.9.24 to 2022.12.7 (#88)

Bumps [certifi](https://github.com/certifi/python-certifi) from 2022.9.24 to 2022.12.7.
- [Release notes](https://github.com/certifi/python-certifi/releases)
- [Commits](https://github.com/certifi/python-certifi/compare/2022.09.24...2022.12.07)

---
updated-dependencies:
- dependency-name: certifi
  dependency-type: direct:production
...

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;

Signed-off-by: dependabot[bot] &lt;support@github.com&gt;
Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`c66052e`](https://github.com/WIPACrepo/rest-tools/commit/c66052e71498e7b9fef65bf402a4d3559806ca2c))


## v1.3.16 (2022-11-17)

###  

* Use `WIPACrepo/wipac-dev-project-action@v1` (#86)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`d1476ef`](https://github.com/WIPACrepo/rest-tools/commit/d1476efc93ab5793eaec18fb411696978341ef77))


## v1.3.15 (2022-11-14)

###  

* dependabot: bump WIPACrepo/wipac-dev-py-setup-action from 1.8 to 1.9 (#83)

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`1264ec9`](https://github.com/WIPACrepo/rest-tools/commit/1264ec901dd14932449f43362a665fbe59d9fb0e))


## v1.3.14 (2022-11-14)

###  

* Auto-Add `dependencies` PRs/Issues to Project (#85)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`ea773aa`](https://github.com/WIPACrepo/rest-tools/commit/ea773aa0d43d8bb0dff6591be993bb71825d041f))


## v1.3.13 (2022-11-08)

###  

* dependabot: bump pyjwt[crypto] from 2.5.0 to 2.6.0 (#80)

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`e6224f6`](https://github.com/WIPACrepo/rest-tools/commit/e6224f6d1b0ce0a2695b298db0261dbe6be88cdf))

* dependabot: bump actions/setup-python from 3 to 4 (#79)

Co-authored-by: dependabot[bot] &lt;49699333+dependabot[bot]@users.noreply.github.com&gt; ([`9b43e24`](https://github.com/WIPACrepo/rest-tools/commit/9b43e24b6cb273657c16ca7e1a9a5a3910a0f01e))


## v1.3.12 (2022-11-08)

###  

* Enable Dependabot Pt-2 (#81)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`f134870`](https://github.com/WIPACrepo/rest-tools/commit/f1348707d81a3dca39b708e8b7762210c68df008))


## v1.3.11 (2022-11-08)

###  

* Enable Dependabot (#78)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`67a1b39`](https://github.com/WIPACrepo/rest-tools/commit/67a1b39bcf3ab37049d24f06d04b747568cc419c))


## v1.3.10 (2022-11-03)

###  

* Fix `ArgumentHandler` Typecasting (#77)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`99273b5`](https://github.com/WIPACrepo/rest-tools/commit/99273b52fc708eb90931524365507d604619ec34))


## v1.3.9 (2022-10-25)

###  

* build for py 3.11 (#76)

* build for py 3.11

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update requirements.txt

* bump version of setup action

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update requirements.txt

* &lt;bot&gt; update requirements-telemetry.txt

* &lt;bot&gt; update requirements-tests.txt

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`12f6b0f`](https://github.com/WIPACrepo/rest-tools/commit/12f6b0f30359c58a93568d79fdacd38dc2ba0a2a))


## v1.3.8 (2022-10-24)

###  

* pin python version until py3.11 gets fully released (#75)

* pin python version until py3.11 gets fully released

* &lt;bot&gt; update setup.cfg

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`9323e56`](https://github.com/WIPACrepo/rest-tools/commit/9323e56ac26ed559060a57b4a6a786fd149f5d4e))

* implement generic keycloak role auth (#73)

* implement generic keycloak role auth

* &lt;bot&gt; update setup.cfg

* debug times on runners

* fix imports for debug

* auth failures are a pyjwt bug. pin for now

* &lt;bot&gt; update requirements.txt

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`11b5901`](https://github.com/WIPACrepo/rest-tools/commit/11b5901717713e361fa37e2add5995ee6e612ed6))

* &lt;bot&gt; update requirements.txt ([`a574f87`](https://github.com/WIPACrepo/rest-tools/commit/a574f872a50e17b38c4e49a1718162c4419a9133))

* create token from service account (#72)

* allow creating the tokens directly from a client id/secret via a service account

* &lt;bot&gt; update requirements.txt

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`fc79fc5`](https://github.com/WIPACrepo/rest-tools/commit/fc79fc5c7ca24fbba49e11cf2f7d5900423b82ff))


## v1.3.7 (2022-09-27)

###  

* &lt;bot&gt; update requirements.txt ([`fa988b2`](https://github.com/WIPACrepo/rest-tools/commit/fa988b28f7889e21bd33abed154b69e64ea73e4b))

* add PKCE support for public OAuth2 clients (#71)

* add PKCE support for public OAuth2 clients

* &lt;bot&gt; update requirements.txt

* add typing hint

* first attempt to fix tests

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`83c98f6`](https://github.com/WIPACrepo/rest-tools/commit/83c98f61c1e4aa8282732fe5c50ffc4e956552cc))


## v1.3.6 (2022-08-09)

###  

* make secret optional. add update_func to pass on token updates. (#70)

* make secret optional. add update_func to pass on token updates.

* fix typing

* fix typing (try 2)

* fix a few bugs when using / not using client secret ([`ae23dd4`](https://github.com/WIPACrepo/rest-tools/commit/ae23dd4abe35961bfde22ed1c2eb3fe6f12ec808))


## v1.3.5 (2022-08-05)

###  

* run tests in github action (#68)

* run tests in CI

* &lt;bot&gt; update setup.cfg

* &lt;bot&gt; update requirements.txt

* update asyncio mode for pytest

* more testing packages

* &lt;bot&gt; update setup.cfg

* add httpretty dependency to testing

* help build local dev env

* require crypto extensions for pyjwt, to get RSA support (#67)

* require crypto extensions for pyjwt, to get RSA support

* &lt;bot&gt; update requirements.txt

Co-authored-by: github-actions &lt;github-actions@github.com&gt;

* bump min python version to 3.7

* &lt;bot&gt; update setup.cfg

* run py-tests on all supported python versions in parallel

* 3.7 syntax

* ignore asyncio deprecation for now

* remove tox. closes #69 by moving all circleci tests into github actions.

* &lt;bot&gt; update README.md

* fix flake8 errors

* bump telemetry to min version

* better typing hints

* deprecations are not errors

* fix f-string = 3.8 feature

* fix integration test

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`9d231b4`](https://github.com/WIPACrepo/rest-tools/commit/9d231b420e9f862c36c6819f2778a72d440f5a75))


## v1.3.4 (2022-08-05)

###  

* require crypto extensions for pyjwt, to get RSA support (#67)

* require crypto extensions for pyjwt, to get RSA support

* &lt;bot&gt; update requirements.txt

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`16d3326`](https://github.com/WIPACrepo/rest-tools/commit/16d3326f56672fd0d084ac979532240e95b18f87))


## v1.3.3 (2022-05-31)

###  

* Bump WIPAC Actions (#66)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`aaf37d6`](https://github.com/WIPACrepo/rest-tools/commit/aaf37d69d8e36d13f5705a556f65cfac189a58e6))


## v1.3.2 (2022-05-31)

###  

* &lt;bot&gt; update requirements.txt ([`8f988df`](https://github.com/WIPACrepo/rest-tools/commit/8f988df3e0a75724219da88d014e5c1f347f1b19))

* Dependency Bumps (Triggered by dependabot) (#64) ([`a1b1467`](https://github.com/WIPACrepo/rest-tools/commit/a1b1467bb357b95bdca6812c58124ca368858c3e))


## v1.3.1 (2022-03-18)

###  

* Use WIPAC GH Action Packages (#63)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`574bf18`](https://github.com/WIPACrepo/rest-tools/commit/574bf183b7ced51198aabf9b4a19f0a616d85da2))


## v1.3.0 (2022-03-16)

###  

* &lt;bot&gt; update requirements.txt ([`56478ee`](https://github.com/WIPACrepo/rest-tools/commit/56478ee548fc32feb94930a5835942603546f1b7))

### [minor]

* Updates for PyPI Publish [minor] (#62)

Co-authored-by: github-actions &lt;github-actions@github.com&gt; ([`0ad4ec7`](https://github.com/WIPACrepo/rest-tools/commit/0ad4ec78426c855b7d349220f673c1b7f47399ed))


## v1.2.5 (2022-01-25)

###  

* Keycloak doesn&#39;t use nbf, so remove it ([`2a3c0b3`](https://github.com/WIPACrepo/rest-tools/commit/2a3c0b316f6eea915136d57b595a5a8df03e3753))


## v1.2.4 (2022-01-24)

###  

* be more secure by validating both aud and iss claims (#59)

* be more secure by validating both aud and iss claims

* fix flake8 errors ([`5bf6e65`](https://github.com/WIPACrepo/rest-tools/commit/5bf6e658e43132325c597e5696d888d1727f899c))


## v1.2.3 (2022-01-18)

###  

* GitHub Linter Actions: flake8 and mypy (#58)

Co-authored-by: Patrick Meade &lt;blinkdog@protonmail.com&gt; ([`f694a1b`](https://github.com/WIPACrepo/rest-tools/commit/f694a1b0d822780220a888835b99a40bd636dfe4))


## v1.2.2 (2022-01-11)

###  

* OIDC (OAuth2) Login Handler (#56)

* Add a handler to do the OpenID Connect login procedure

* some fixes after prod testing with keycloak

* remove extra fixtures that were copied in

* use float()

* disable mypy and flake8 in circleci, pending #57

* properly disable mypy ([`4f2c785`](https://github.com/WIPACrepo/rest-tools/commit/4f2c785ffb2ab30f6a9fabdfbbfb3a6b7c096533))


## v1.2.1 (2021-12-29)

###  

* allow adding headers to a request ([`f44a943`](https://github.com/WIPACrepo/rest-tools/commit/f44a943435371f1e326a67267cff004080ff10fb))


## v1.2.0 (2021-11-19)

### [minor]

* [minor] Move More Modules to `utils` Sub-Package (#54) ([`7244afc`](https://github.com/WIPACrepo/rest-tools/commit/7244afca10e62dc1c53fe1d35d406841e09babc8))


## v1.1.26 (2021-11-16)

###  

* Refactor AsyncSession and Session API to keep up with requests dependency (#50)

* Refactor API to keep up with requests dependency

* Make sure urllib3 is also using allowed_methods ([`83e78b4`](https://github.com/WIPACrepo/rest-tools/commit/83e78b45b07c924d89485b7e8440f9f24eac0cea))


## v1.1.25 (2021-11-16)

###  

* Method-Based Span Name for `RestClient` (#51) ([`722beba`](https://github.com/WIPACrepo/rest-tools/commit/722bebacaaefdbb7cec41060a1f3b1e67fae1be2))


## v1.1.24 (2021-11-16)

###  

* Method-Based Span Name (#49) ([`f9a3842`](https://github.com/WIPACrepo/rest-tools/commit/f9a3842ec1dc61954a8b51ee8857730abe62b893))


## v1.1.23 (2021-11-10)

###  

* Add Exports to All Sub-Packages (#48) ([`c951ef8`](https://github.com/WIPACrepo/rest-tools/commit/c951ef8fde5a255746b29f8c9f7f85e4ad747368))


## v1.1.22 (2021-11-10)

###  

* Bump `wipac_telemetry` to v0.1.24 (#47) ([`a4edcae`](https://github.com/WIPACrepo/rest-tools/commit/a4edcae25875aa386a6aa7aac1f784ff038460fe))


## v1.1.21 (2021-11-10)

###  

* Add Exportable Typings for Package (#46) ([`700c9d4`](https://github.com/WIPACrepo/rest-tools/commit/700c9d4193d0a85a13199c76ec33655ad853da31))


## v1.1.20 (2021-11-04)

###  

* Bump `wipac_telemetry` v0.1.21 (#45) ([`a8f9b7d`](https://github.com/WIPACrepo/rest-tools/commit/a8f9b7d7c326a96f47ef5333f32f2a1cac005bbf))


## v1.1.19 (2021-11-02)

###  

* Remove Overriding Logging Level Bug (#43) ([`4176093`](https://github.com/WIPACrepo/rest-tools/commit/4176093c9745164afc5dfe96165235ad98b5a427))


## v1.1.18 (2021-11-01)

###  

* Bump wipac_telemetry dependency to v0.1.19 (#42) ([`0e320cb`](https://github.com/WIPACrepo/rest-tools/commit/0e320cb8f293176cca0f7230f9dbbde30588511b))


## v1.1.17 (2021-10-29)

###  

* Bump wipac_telemetry dependency to v0.1.18 (#41) ([`24128bc`](https://github.com/WIPACrepo/rest-tools/commit/24128bc2e9529daab86108edc8579f8723ae58de))


## v1.1.16 (2021-10-19)

###  

* Mypy Fix (#40) ([`6922b84`](https://github.com/WIPACrepo/rest-tools/commit/6922b8437048df6862181eb4a23b91a7efeb9f55))


## v1.1.15 (2021-10-19)

###  

* fix checking expiration of access_token, for newer versions of pyJWT ([`933ae85`](https://github.com/WIPACrepo/rest-tools/commit/933ae85bc04e68df422c1a4200ef861b135e6971))


## v1.1.14 (2021-09-28)

###  

* Bump wipac_telemetry dependency to v0.1.16 (#39) ([`181ecef`](https://github.com/WIPACrepo/rest-tools/commit/181ecef9841913f6f454ee1b9f57e4bd9b8cc83e))


## v1.1.13 (2021-09-27)

###  

* Bump wipac_telemetry dependency to v0.1.15 (#38) ([`8717ce1`](https://github.com/WIPACrepo/rest-tools/commit/8717ce109840ae0073f7b9c3b09f88e890cba09a))


## v1.1.12 (2021-09-16)

###  

* wipac_telemetry @ 0.1.14 (#37) ([`39699b2`](https://github.com/WIPACrepo/rest-tools/commit/39699b2ee6bade2e8df4ebc2eaf3698ceaff3543))


## v1.1.11 (2021-08-25)

###  

* Move `types-requests` to Dev Reqs (#36) ([`0fc6b47`](https://github.com/WIPACrepo/rest-tools/commit/0fc6b4742922dcc2782869ab4d9fb43cc412476c))


## v1.1.10 (2021-08-23)

###  

* Minimize `requirements.txt`, Add `requirements-dev.txt` (#35) ([`b77e2b7`](https://github.com/WIPACrepo/rest-tools/commit/b77e2b71bc7fb551c1296c757c2d8ae9203ffc91))


## v1.1.9 (2021-08-23)

###  

* Minimize `requirements.txt`: remove `pycycle` (#34) ([`5147a17`](https://github.com/WIPACrepo/rest-tools/commit/5147a17aff2d0188833497bea289889fc30ed0cc))


## v1.1.8 (2021-08-23)

###  

* Upgrade `wipac_telemetry` Requirement (#33) ([`a07e3f1`](https://github.com/WIPACrepo/rest-tools/commit/a07e3f141344017b2f79768ab4642ee98f04d682))


## v1.1.7 (2021-08-09)

###  

* Introduce WIPAC Telemetry (#26)

* require `wipac-telemetry-prototype/wipac_tracing`

* require `wipac-telemetry-prototype/wipac_telemetry` (fix)

* add `@tracing.tools.new_span()` to RestClient&#39;s public methods (typing?)

* `new_span` -&gt; `spanned`

* add `these` args to `@spanned()`; make open &amp; close evented

* remove `@evented()` from open and close b/c async stuff

* add span injection

* RestClient: inject span &amp; send Link over the wire

* RestHandler: add decorator for using Link sent from client (for a span)

* add common arg name for link REST argument

* add common arg name for link REST argument - 2

* strip manual instrumentation in favor of http-header based propagation

* use `propagations.inject`

* add client-server example/test

* appease the linters

* make client-server test more realistic; use string syntax for span kind

* record requester&#39;s role as span attribute; move decorator within auth

* appease flake8

* move RestHandler tracing to base RestHandler class (aka auto-instrument)

* span `_execute` to use `get_current_span()` downstream + guarantee end()

* record `self.request.path` as attribute instead of entire `uri`

* use SpanKind.CLIENT enum; import `tracing_tools`&#39;s members by name

* update to latest WIPACTel syntax

* incorporate carrier-updates; shell script to run client &amp; server example

* Added guard in RestHandler.get_current_user

* Added types-requests to requirements.txt to satisfy CircleCI

* Add version to wipac-telemetry-prototype to satisfy Try Setup Install

* Minor changes to project metadata

Co-authored-by: Patrick Meade &lt;blinkdog@protonmail.com&gt; ([`43196f9`](https://github.com/WIPACrepo/rest-tools/commit/43196f975fe9955165ba7adc38299a261463e8ff))


## v1.1.6 (2021-05-27)

###  

* Bump `wipac-dev-tools` (#32) ([`1d334ee`](https://github.com/WIPACrepo/rest-tools/commit/1d334eecbb31d062b1125d49a6987e398ad61354))


## v1.1.5 (2021-05-27)

###  

* Setup Updates: SetupShop and GH Action (#31) ([`b5a4ffd`](https://github.com/WIPACrepo/rest-tools/commit/b5a4ffda27b57f4928140fecb095781219fa9402))


## v1.1.4 (2021-05-13)

###  

* Handle GitHub Package Reqs per PEP 805 URL - 3 (#30) ([`32ee9b0`](https://github.com/WIPACrepo/rest-tools/commit/32ee9b0b63afcf8776b2b5e3c851bc33d4e07762))


## v1.1.3 (2021-05-13)

###  

* Handle GitHub Package Reqs per PEP 805 URL - 2 (#29) ([`9599672`](https://github.com/WIPACrepo/rest-tools/commit/95996720c1c67d524847050ff739bc84c3a76963))


## v1.1.2 (2021-05-13)

###  

* Handle GitHub Package Reqs per PEP 805 URL (#28) ([`142dfdf`](https://github.com/WIPACrepo/rest-tools/commit/142dfdfbf8133b8f4f01638320575876b9275a12))


## v1.1.1 (2021-05-13)

###  

* Redirect to `wipac_dev_tools.from_environment()` (#27) ([`4d908a3`](https://github.com/WIPACrepo/rest-tools/commit/4d908a30811ce849f5204911004523b5236e4d30))


## v1.1.0 (2021-03-24)

### [minor]

* Make Streaming Compatible for Python &lt;3.8 (#23) [minor] ([`0d05bba`](https://github.com/WIPACrepo/rest-tools/commit/0d05bba5e7ba9180e737fdc5a161070729c51edf))


## v1.0.10 (2021-03-24)

###  

* decrease open() (&#39;establish REST http session&#39;) logging to debug (#22) ([`16d39fc`](https://github.com/WIPACrepo/rest-tools/commit/16d39fce7fe8c408a98b13eec4ccb5ca08d6c086))


## v1.0.9 (2021-03-24)

###  

* pass through max_body_size to the HTTPServer ([`23626ad`](https://github.com/WIPACrepo/rest-tools/commit/23626add06d1229158ac87b9a1c7e79d851f1383))


## v1.0.8 (2021-03-24)

###  

* NDJSON-Compliant Request Streaming (#19) ([`757cc7f`](https://github.com/WIPACrepo/rest-tools/commit/757cc7f953932b66778146a3aec988482c050611))


## v1.0.7 (2021-03-11)

###  

* Semantic Release GH Action (#17) ([`851eb8e`](https://github.com/WIPACrepo/rest-tools/commit/851eb8ecb15bb1333aea56ab3c710ca570f0f010))

* setup.py: one-liner fix for version-parsing ([`0557e76`](https://github.com/WIPACrepo/rest-tools/commit/0557e76b37955efdecb980110c65b98b99577500))

* ArgumentHandler Default Bug Fix (#16)

* fix type-checking default value bug

* bump to 1.0.4

* test default getting ([`54cc6b9`](https://github.com/WIPACrepo/rest-tools/commit/54cc6b913f44fd1c4678c57ae0aac6f5e2519f2d))

* update version to 1.0.3 ([`588bb77`](https://github.com/WIPACrepo/rest-tools/commit/588bb77f3a0a3ed0bccf3781c2d602aeaeabfe2d))

* Argument Handler No Default Error Message (#15)

* add more detail for missing argument cases

* override log_message, and preserve the MissingArgumentError instance

* override `error.reason`; consolidate testing ([`d21ae53`](https://github.com/WIPACrepo/rest-tools/commit/d21ae536c275e13af8391f80d6ca000b69691c99))

* ArgumentHandler: Add Type-Checking for Body Arguments + Forbiddens List (#13)

* add `type_` to get_json_body_argument() -- no effect, yet

* remove call to _qualify_argument() for json_arg; comments

* add _type_check() calls in get_json_body_argument(), raise _UnqualifiedArgumentError

* _type_check(): add server_side_error; test that

* add return value to _type_check(); tests

* separate _qualify_argument() into _cast_type() &amp; _validate_choice()

* swap positional arguments in qualification functions

* add `forbiddens` optional list arg (&amp; test)

* add empty list &amp; dict forbiddens-checks

* at API-level: refactor `type_` to `type`; after all, argparse does it (https://docs.python.org/3/library/argparse.html#type) ([`c852096`](https://github.com/WIPACrepo/rest-tools/commit/c85209680c1ee6de031f4b0d93db7b2145a9bf0f))

* ArgumentParser, MyPy, Flake8, &amp; Circular Import Fixes (#10)

* mv client/json_util.py -&gt; utils/json_utils.py

* add pycycle; sort requirements.txt

* pytest: add --mypy and --flake8

* mypy &amp; flake8 - 1

* mypy-fix: from_environment()

* fixed RestHandler&#39;s calls to ArgumentHandler, now tests via RestHandler

* setup.py: add rest_tools.utils

* cleanup syntax ([`981c683`](https://github.com/WIPACrepo/rest-tools/commit/981c683c683c9b92f750753a126803c79db0edd2))

* Helper Methods for Handling REST &amp; JSON-Body Arguments (#3)

* add methods

* move json_decode import

* shooting from the hip with these imports...

* get_query_argument() -&gt; get_argument()

* comments

* proposed method merging; also .gitignore

* add optional casting--mimic `argparse`

* syntax error; comments

* remove argument-helper code (moving to own file)

* light-cleanup; fix super-reference bug in get_template_namespace()

* handler.py: add ArgumentHandler forwarding

* handler.py: add ArgumentHandler forwarding - 2

* add argument_handler.py with latest updates: namely, `choices` argument

* NO_DEFAULT reference bug fix

* argument_handler.py -&gt; arghandler.py; move NO_DEFAULT to module level

* stub out tests

* test _qualify_argument

* test _type_check()

* test _get_json_body_argument()

* get_json_body_argument(): remove `strip` and `type_` arguemnts

* get_json_body_argument(): remove `strip` and `type_` arguemnts - 2

* test get_argument() (w/ json body parsing)

* arghandler.py/get_argument(): pass NO_DEFAULT to get_json_body_argument

* standardize 400 error formatting

* check for _UnqualifiedArgumentError

* standardize 400 error formatting - 2

* test test get_argument() -- tests_40+

* remove double-400 in error messages

* remove double-400 in error messages - 2

* update block comments

* use `bool(distutils.util.strtobool(value))` for type-casting bool args

* _get_json_body() -&gt; _get_json_body_arguments()

* bug fix: json_body not json ([`fee14ea`](https://github.com/WIPACrepo/rest-tools/commit/fee14ea3ec717bf1ebe2f08e6581bfc611f5c821))

### .

* 1.0.6 ([`7d6f4ed`](https://github.com/WIPACrepo/rest-tools/commit/7d6f4ed244a10c2974c725f02aa0671e4d410005))

* 1.0.5 ([`6795273`](https://github.com/WIPACrepo/rest-tools/commit/67952735d3f488266e04f512514563020269bc05))


## v1.0.0 (2021-02-15)

###  

* setup.py: add PyJWT&gt;=2.0.1 (#9) ([`6a4ddac`](https://github.com/WIPACrepo/rest-tools/commit/6a4ddac80c8cf7eda8c286b6ffeabcc5f5dd18bf))

* RestClient Module-Level Logging (#7)

* .gitignore: add src/

* add RestClient module-level logger

* PyJWT&#39;s `jwt.encode()` fix

* README.md: add CircleCI badge

* PyJWT&#39;s `jwt.decode()` fix

* require pyjwt &gt;= 2.0.1 ([`8a0e317`](https://github.com/WIPACrepo/rest-tools/commit/8a0e3177f8e2f8a3366eab859e3b1b1c7310507e))

* disable route_stats if it is not properly configured ([`e5cb0d2`](https://github.com/WIPACrepo/rest-tools/commit/e5cb0d21284357c26bd923f7936109995d22db41))

* fix seq requests ([`c842045`](https://github.com/WIPACrepo/rest-tools/commit/c84204594a8e599ed733d00ee4233e1751ae7229))

* update readme and examples ([`650218e`](https://github.com/WIPACrepo/rest-tools/commit/650218e2f814e79b7407b80e8d5fb9a2ffcfd1fd))


## v0.2.0 (2020-08-10)

###  

* fix empty case, and add a test for it ([`d07c78c`](https://github.com/WIPACrepo/rest-tools/commit/d07c78c0978f6f581e50db89a156a3103a2f2fb9))

* retire old RouteStats. enable tests ([`fc39bf4`](https://github.com/WIPACrepo/rest-tools/commit/fc39bf496ddcb0130a1a0f2846240dafe7671334))

* enforce 503 backoff if we hit request time limits ([`856fbb4`](https://github.com/WIPACrepo/rest-tools/commit/856fbb44a3de1ba80cacf730efe29fc0804433b8))

* need to check expire time against the future, not the past ([`9745d73`](https://github.com/WIPACrepo/rest-tools/commit/9745d73c482703ac256a30fb515b1212c1923237))

* allow rest client to take a function to generate the token ([`e9539a8`](https://github.com/WIPACrepo/rest-tools/commit/e9539a86e69aba3972dfa94ff68b280bd1f63efc))

* remove unused line ([`a80fefb`](https://github.com/WIPACrepo/rest-tools/commit/a80fefb0137436e9fe5e827507b0b609679bec34))

* add OpenID refresh token REST client ([`ea20404`](https://github.com/WIPACrepo/rest-tools/commit/ea204047653e142410f4b5a5844ee134c5624e24))

* lower logging level on messages ([`66eb2e9`](https://github.com/WIPACrepo/rest-tools/commit/66eb2e9272725a73124fb4c51999078a2ed73867))

* properly stop the server by closing all connections. useful for unit tests to not leave coroutines hanging. ([`6d52abe`](https://github.com/WIPACrepo/rest-tools/commit/6d52abe3e8b97712c22047a6d69ba6705fd1dd68))

* fix openid auth ([`395c4d5`](https://github.com/WIPACrepo/rest-tools/commit/395c4d50e4ec493f1518a55df285a3634239fe02))

* add OpenID auth, for Keycloak support ([`2d3d61f`](https://github.com/WIPACrepo/rest-tools/commit/2d3d61f37bf92f3dd53fda2761156e852503a1de))

* make flake8 happy, and @blinkdog too ([`c2ed82a`](https://github.com/WIPACrepo/rest-tools/commit/c2ed82a730253b178d24f00952d9a5b09ece7acd))

* allow automatic typing of config variables from env. add some tests (#1)

allow automatic typing of config variables from env. add some tests ([`87f050c`](https://github.com/WIPACrepo/rest-tools/commit/87f050c7ad34a13933722dd80231165473c9e673))

* add import for from_environment ([`cdfeacd`](https://github.com/WIPACrepo/rest-tools/commit/cdfeacdaafd546ed96821ce57d646146ed75a9e4))

* Add config.py from lta ([`e8e799f`](https://github.com/WIPACrepo/rest-tools/commit/e8e799f839f339a7fa48516035a30eb6a1f1c0ed))

* skip logging for DELETE 404 errors, as this is expected ([`197e5c1`](https://github.com/WIPACrepo/rest-tools/commit/197e5c17dd6d3aa7ba7dc0d9b9b2e0a620019c6e))

* need cryptography for RS algorithms ([`74b241a`](https://github.com/WIPACrepo/rest-tools/commit/74b241a7cd83f30b2bf5effac3e2b705dc867a4c))

* make token optional ([`4434eda`](https://github.com/WIPACrepo/rest-tools/commit/4434eda277a102ad48959ed7f13c794a8996febd))

* handle multiple token roles correctly ([`187c8ce`](https://github.com/WIPACrepo/rest-tools/commit/187c8ced022fb6fa8516128772ca75b8d888b3d1))

* add handy short import ([`0ca3f44`](https://github.com/WIPACrepo/rest-tools/commit/0ca3f445b971c709d7223c05084dd75800b0a7ec))

* upgrade for token service scope-rbac handling ([`fe4cc14`](https://github.com/WIPACrepo/rest-tools/commit/fe4cc147fe3f6550de193733a78a47a4900daf3f))

* try to automatically accept the ANY audience ([`3603a87`](https://github.com/WIPACrepo/rest-tools/commit/3603a87fcdc98feffc22603c53e9dad113afc30a))

* fix version ([`c396f41`](https://github.com/WIPACrepo/rest-tools/commit/c396f41eb37f0819bcd17173d394d0330269a409))

* allow taking two secrets for public/private keys ([`6807245`](https://github.com/WIPACrepo/rest-tools/commit/680724565a9c0d2d261b36d1e01f2713672f612a))

* add common code for daemonizing a server ([`6601682`](https://github.com/WIPACrepo/rest-tools/commit/66016820552c6e3452a2d45413772ca53fc4c1e2))

* actually return a string instead of bytes ([`0009385`](https://github.com/WIPACrepo/rest-tools/commit/000938523ffe370c4a6cd68ccda3a811767d942d))

* pass through advanced options for validation ([`9f54643`](https://github.com/WIPACrepo/rest-tools/commit/9f5464342f8acbb12bfb619677d808ef1f7b5c6e))


## v0.1.0 (2019-01-11)

###  

* automatic string conversion for tokens ([`344c020`](https://github.com/WIPACrepo/rest-tools/commit/344c0205875e53a8503cd98410a9d80adf79e5d7))

* add auth algorithm to handler config ([`fd9849c`](https://github.com/WIPACrepo/rest-tools/commit/fd9849ca16c7d1c9f62554d30b819ee047e7a4f9))

* fix retries, so you can disable them in testing ([`5251067`](https://github.com/WIPACrepo/rest-tools/commit/525106724b50a703d71c7299e15ab165e8e58615))

* clean up copy/paste errors ([`e3a1763`](https://github.com/WIPACrepo/rest-tools/commit/e3a1763f3f77e8a3a0dcc71c25a89cc44a670b22))

* add stop method ([`c40be79`](https://github.com/WIPACrepo/rest-tools/commit/c40be795d6187ec64aa9c4fde90b803f7d787589))

* fix names ([`cae3e5a`](https://github.com/WIPACrepo/rest-tools/commit/cae3e5aa0e0b6ee6dc207c1e45aa902b6ed958ed))

* basic rest tools, with an example of usage ([`d620c13`](https://github.com/WIPACrepo/rest-tools/commit/d620c13847b2af232fd4cb1cac03d0ff74671d59))

* basic setup ([`b757582`](https://github.com/WIPACrepo/rest-tools/commit/b75758272783f22a7c05d18c2ea965749e779509))

* Initial commit ([`31203d2`](https://github.com/WIPACrepo/rest-tools/commit/31203d2af9fe76a10285af8cfa44df6bdca88e17))
