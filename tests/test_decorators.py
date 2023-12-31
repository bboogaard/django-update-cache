import json
from unittest import mock

from django.test import RequestFactory
from django.test.testcases import TestCase
from freezegun import freeze_time
from update_cache import brokers
from update_cache.cache.cache import make_cache_key, make_view_cache_key, missing

from testapp import cached_functions, utils, views
from testapp.cached_functions import random


class TestDecorators(TestCase):

    @mock.patch.object(cached_functions, 'get_random_string')
    def test_cache_function(self, get_string):
        get_string.side_effect = [
            100 * 'a',
            100 * 'b'
        ]
        cache = cached_functions.create_random_strings.cache

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = cached_functions.create_random_strings(1)
        self.assertEqual(cache.get_active(make_cache_key(
            cached_functions.create_random_strings, ((1,), {})
        )).result, [100 * 'a'])
        self.assertEqual(get_string.call_count, 1)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = cached_functions.create_random_strings(1)
        self.assertEqual(get_string.call_count, 1)
        # After caching, results should be equal
        self.assertEqual(result1, result2)

        with freeze_time('2023-12-01T10:05:00Z'):
            result3 = cached_functions.create_random_strings(1)
        self.assertEqual(cache.get_expired(make_cache_key(
            cached_functions.create_random_strings, ((1,), {})
        )).result, [100 * 'a'])
        self.assertEqual(get_string.call_count, 1)
        # 5 mins later, cache has expired, results should be still be equal
        self.assertEqual(result1, result3)

        with freeze_time('2023-12-01T10:05:01Z'):
            result4 = cached_functions.create_random_strings(1)
        self.assertEqual(cache.get_active(make_cache_key(
            cached_functions.create_random_strings, ((1,), {})
        )).result, [100 * 'b'])
        self.assertEqual(get_string.call_count, 2)
        # Getting expired result, results should be still be equal
        self.assertEqual(result1, result4)

        with freeze_time('2023-12-01T10:05:02Z'):
            result5 = cached_functions.create_random_strings(1)
        self.assertEqual(get_string.call_count, 2)
        # Cache should have been updated now
        self.assertNotEqual(result1, result5)

    @mock.patch.object(random, 'randint')
    def test_cache_function_with_custom_timeout(self, get_int):
        get_int.side_effect = [
            100 * '1',
            100 * '2'
        ]
        cache = cached_functions.create_random_numbers.cache

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = cached_functions.create_random_numbers(1)
        self.assertEqual(cache.get_active(make_cache_key(
            cached_functions.create_random_numbers, ((1,), {})
        )).result, [100 * '1'])
        self.assertEqual(get_int.call_count, 1)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = cached_functions.create_random_numbers(1)
        self.assertEqual(get_int.call_count, 1)
        # After caching, results should be equal
        self.assertEqual(result1, result2)

        with freeze_time('2023-12-01T10:01:00Z'):
            result3 = cached_functions.create_random_numbers(1)
        self.assertEqual(cache.get_expired(make_cache_key(
            cached_functions.create_random_numbers, ((1,), {})
        )).result, [100 * '1'])
        self.assertEqual(get_int.call_count, 1)
        # 1 min later, cache has expired, results should be still be equal
        self.assertEqual(result1, result3)

        with freeze_time('2023-12-01T10:01:01Z'):
            result4 = cached_functions.create_random_numbers(1)
        self.assertEqual(cache.get_active(make_cache_key(
            cached_functions.create_random_numbers, ((1,), {})
        )).result, [100 * '2'])
        self.assertEqual(get_int.call_count, 2)
        # Getting expired result, results should be still be equal
        self.assertEqual(result1, result4)

        with freeze_time('2023-12-01T10:01:02Z'):
            result5 = cached_functions.create_random_numbers(1)
        self.assertEqual(get_int.call_count, 2)
        # Cache should have been updated now
        self.assertNotEqual(result1, result5)

    @mock.patch.object(brokers, 'enqueue')
    @mock.patch.object(random, 'choice')
    def test_cache_function_with_async_broker(self, get_choice, mock_enqueue):
        get_choice.return_value = 'A'
        cache = cached_functions.create_random_letters.cache

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = cached_functions.create_random_letters(1)
        self.assertEqual(cache.get_active(make_cache_key(
            cached_functions.create_random_letters, ((1,), {})
        )).result, ['A'])
        self.assertEqual(get_choice.call_count, 1)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = cached_functions.create_random_letters(1)
        self.assertEqual(get_choice.call_count, 1)
        # After caching, results should be equal
        self.assertEqual(result1, result2)

        with freeze_time('2023-12-01T10:05:00Z'):
            result3 = cached_functions.create_random_letters(1)
        self.assertEqual(cache.get_expired(make_cache_key(
            cached_functions.create_random_letters, ((1,), {})
        )).result, ['A'])
        self.assertEqual(get_choice.call_count, 1)
        # 5 mins later, cache has expired, results should be still be equal
        self.assertEqual(result1, result3)

        with freeze_time('2023-12-01T10:05:01Z'):
            result4 = cached_functions.create_random_letters(1)
        self.assertEqual(get_choice.call_count, 1)
        # Getting expired result, results should be still be equal
        self.assertTrue(mock_enqueue.called)
        self.assertEqual(result1, result4)

    @mock.patch.object(random, 'choice')
    def test_cache_function_with_custom_backend(self, get_choice):
        get_choice.side_effect = [
            'Foo',
            'Bar'
        ]
        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = cached_functions.create_random_words(1)
        self.assertEqual(get_choice.call_count, 1)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = cached_functions.create_random_words(1)
        self.assertEqual(get_choice.call_count, 2)
        # After caching, results should not be equal, because we use dummy cache
        self.assertNotEqual(result1, result2)

    @mock.patch.object(utils, 'get_random_string')
    def test_cache_view(self, get_string):
        get_string.side_effect = 100 * [10 * 'a'] + 100 * [10 * 'b'] + 100 * [10 * 'c']
        cache = views.short_strings.cache
        request = RequestFactory().get('/testapp/short_strings/')

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = self._get_response('/testapp/short_strings/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'GET'
        )).result.content.decode(), '\n'.join(100 * [10 * 'a']))
        self.assertEqual(get_string.call_count, 100)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = self._get_response('/testapp/short_strings/')
        self.assertEqual(get_string.call_count, 100)
        # After caching, results should be equal
        self.assertEqual(result1, result2)

        with freeze_time('2023-12-01T10:05:00Z'):
            result3 = self._get_response('/testapp/short_strings/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'GET'
        )).result.content.decode(), '\n'.join(100 * [10 * 'b']))
        self.assertEqual(get_string.call_count, 200)
        # 5 mins later, cache has expired, we should get a new result
        self.assertNotEqual(result1, result3)

        other_request = RequestFactory().get('/testapp/short_strings/?foo=bar')

        with freeze_time('2023-12-01T10:00:01Z'):
            other_result = self._get_response('/testapp/short_strings/?foo=bar')
        self.assertEqual(cache.get_active(make_view_cache_key(
            other_request, 'GET'
        )).result.content.decode(), '\n'.join(100 * [10 * 'c']))
        self.assertEqual(get_string.call_count, 300)
        # Get params should give a new live result
        self.assertNotEqual(result1, other_result)

    @mock.patch.object(random, 'choice')
    def test_cache_view_with_custom_timeout(self, get_choice):
        get_choice.side_effect = 100 * ['a'] + 100 * ['b'] + 100 * ['c']

        cache = views.LowerCaseLetters.get.cache
        request = RequestFactory().get('/testapp/lowercase_letters/')

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = self._get_response('/testapp/lowercase_letters/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'GET'
        )).result.content.decode(), json.dumps('\n'.join(100 * ['a'])))
        self.assertEqual(get_choice.call_count, 100)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = self._get_response('/testapp/lowercase_letters/')
        self.assertEqual(get_choice.call_count, 100)
        # After caching, results should be equal
        self.assertEqual(result1, result2)

        with freeze_time('2023-12-01T10:01:00Z'):
            result3 = self._get_response('/testapp/lowercase_letters/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'GET'
        )).result.content.decode(), json.dumps('\n'.join(100 * ['b'])))
        self.assertEqual(get_choice.call_count, 200)
        # 1 min later, cache has expired, we should get a new result
        self.assertNotEqual(result1, result3)

        other_request = RequestFactory().get('/testapp/lowercase_letters/?foo=bar')

        with freeze_time('2023-12-01T10:00:01Z'):
            other_result = self._get_response('/testapp/lowercase_letters/?foo=bar')
        self.assertEqual(cache.get_active(make_view_cache_key(
            other_request, 'GET'
        )).result.content.decode(), json.dumps('\n'.join(100 * ['c'])))
        self.assertEqual(get_choice.call_count, 300)
        # Get params should give a new live result
        self.assertNotEqual(result1, other_result)

    @mock.patch.object(random, 'randint')
    def test_cache_view_with_custom_backend(self, get_int):
        get_int.side_effect = 100 * [10 * '1'] + 100 * [10 * '2']

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = self._get_response('/testapp/low_numbers/')
        self.assertEqual(get_int.call_count, 100)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = self._get_response('/testapp/low_numbers/')
        self.assertEqual(get_int.call_count, 200)
        # After caching, results should not be equal, because we use dummy cache
        self.assertNotEqual(result1, result2)

    @mock.patch.object(utils, 'get_random_string')
    def test_cache_view_do_not_cache_post(self, get_string):
        get_string.side_effect = 100 * [10 * 'a'] + 100 * [10 * 'b']
        cache = views.short_strings.cache
        request = RequestFactory().post('/testapp/short_strings/', {})

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = self._post_response('/testapp/short_strings/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'POST'
        )), missing)
        self.assertEqual(get_string.call_count, 100)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = self._post_response('/testapp/short_strings/')
        self.assertEqual(get_string.call_count, 200)
        # Results should be different, since we don't cache for post requests
        self.assertNotEqual(result1, result2)

    @mock.patch.object(random, 'choice')
    def test_cache_view_do_not_cache_streaming(self, get_choice):
        get_choice.side_effect = 100 * ['Lorem'] + 100 * ['Ipsum']
        cache = views.lorem_words.cache
        request = RequestFactory().get('/testapp/lorem_words/')

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = self._get_streaming('/testapp/lorem_words/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'GET'
        )), missing)
        self.assertEqual(get_choice.call_count, 100)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = self._get_streaming('/testapp/lorem_words/')
        self.assertEqual(get_choice.call_count, 200)
        # Results should be different, since we don't cache for streaming requests
        self.assertNotEqual(result1, result2)

    @mock.patch.object(utils, 'get_random_string')
    def test_cache_view_do_not_cache_disallowed_status(self, get_string):
        get_string.side_effect = 100 * [10 * 'a'] + 100 * [10 * 'b']
        cache = views.error.cache
        request = RequestFactory().get('/testapp/error/')

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = self._get_response('/testapp/error/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'GET'
        )), missing)
        self.assertEqual(get_string.call_count, 100)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = self._get_response('/testapp/error/')
        self.assertEqual(get_string.call_count, 200)
        # Results should be different, since we don't cache for status codes other than 200/304
        self.assertNotEqual(result1, result2)

    @mock.patch.object(utils, 'get_random_string')
    def test_cache_view_do_not_cache_vary_header_cookie(self, get_string):
        get_string.side_effect = 100 * [10 * 'a'] + 100 * [10 * 'b']
        cache = views.with_cookie.cache
        request = RequestFactory().get('/testapp/with_cookie/')

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = self._get_response('/testapp/with_cookie/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'GET'
        )), missing)
        self.assertEqual(get_string.call_count, 100)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = self._get_response('/testapp/with_cookie/')
        self.assertEqual(get_string.call_count, 200)
        # Results should be different, since we don't cache for responses with cookies and Vary header containing
        # 'Cookie'
        self.assertNotEqual(result1, result2)

    @mock.patch.object(utils, 'get_random_string')
    def test_cache_view_do_not_cache_cache_control_private(self, get_string):
        get_string.side_effect = 100 * [10 * 'a'] + 100 * [10 * 'b']
        cache = views.private_cache.cache
        request = RequestFactory().get('/testapp/private_cache/')

        with freeze_time('2023-12-01T10:00:00Z'):
            result1 = self._get_response('/testapp/private_cache/')
        self.assertEqual(cache.get_active(make_view_cache_key(
            request, 'GET'
        )), missing)
        self.assertEqual(get_string.call_count, 100)
        with freeze_time('2023-12-01T10:00:01Z'):
            result2 = self._get_response('/testapp/private_cache/')
        self.assertEqual(get_string.call_count, 200)
        # Results should be different, since we don't cache for responses with Cache-Control: private
        self.assertNotEqual(result1, result2)

    def _get_response(self, url):
        response = self.client.get(url)
        return response.content

    def _post_response(self, url):
        response = self.client.post(url, {})
        return response.content

    def _get_streaming(self, url):
        response = self.client.get(url)
        return b''.join(response.streaming_content)
