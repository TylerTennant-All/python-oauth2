"""
The MIT License
 
Copyright (c) 2009 Vic Fryzel
 
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
 
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import unittest
import oauth

class TestError(unittest.TestCase):
    def test_message(self):
        try:
            raise oauth.Error
        except oauth.Error, e:
            self.assertEqual(e.message, 'OAuth error occured.')
        msg = 'OMG THINGS BROKE!!!!'
        try:
            raise oauth.Error(msg)
        except oauth.Error, e:
            self.assertEqual(e.message, msg)

class TestGenerateFunctions(unittest.TestCase):
    def test_build_auth_header(self):
        header = oauth.build_authenticate_header()
        self.assertEqual(header['WWW-Authenticate'], 'OAuth realm=""')
        self.assertEqual(len(header), 1)
        realm = 'http://example.myrealm.com/'
        header = oauth.build_authenticate_header(realm)
        self.assertEqual(header['WWW-Authenticate'], 'OAuth realm="%s"' %
                         realm)
        self.assertEqual(len(header), 1)
    
    def test_escape(self):
        string = 'http://whatever.com/~someuser/?test=test&other=other'
        self.assert_('~' in oauth.escape(string))
        string = '../../../../../../../etc/passwd'
        self.assert_('../' not in oauth.escape(string))

    def test_gen_nonce(self):
        nonce = oauth.generate_nonce()
        self.assertEqual(len(nonce), 8)
        nonce = oauth.generate_nonce(20)
        self.assertEqual(len(nonce), 20)

    def test_gen_verifier(self):
        verifier = oauth.generate_verifier()
        self.assertEqual(len(verifier), 8)
        verifier = oauth.generate_verifier(16)
        self.assertEqual(len(verifier), 16)

class TestConsumer(unittest.TestCase):
    def test_init(self):
        key = 'my-key'
        secret = 'my-secret'
        consumer = oauth.Consumer(key, secret)
        self.assertEqual(consumer.key, key)
        self.assertEqual(consumer.secret, secret)

    def test_basic(self):
        self.assertRaises(ValueError, lambda: oauth.Consumer(None, None))
        self.assertRaises(ValueError, lambda: oauth.Consumer('asf', None))
        self.assertRaises(ValueError, lambda: oauth.Consumer(None, 'dasf'))

class TestToken(unittest.TestCase):
    def setUp(self):
        self.key = 'my-key'
        self.secret = 'my-secret'
        self.token = oauth.Token(self.key, self.secret)

    def test_basic(self):
        self.assertRaises(ValueError, lambda: oauth.Token(None, None))
        self.assertRaises(ValueError, lambda: oauth.Token('asf', None))
        self.assertRaises(ValueError, lambda: oauth.Token(None, 'dasf'))

    def test_init(self):
        self.assertEqual(self.token.key, self.key)
        self.assertEqual(self.token.secret, self.secret)
        self.assertEqual(self.token.callback, None)
        self.assertEqual(self.token.callback_confirmed, None)
        self.assertEqual(self.token.verifier, None)

    def test_set_callback(self):
        self.assertEqual(self.token.callback, None)
        self.assertEqual(self.token.callback_confirmed, None)
        cb = 'http://www.example.com/my-callback'
        self.token.set_callback(cb)
        self.assertEqual(self.token.callback, cb)
        self.assertEqual(self.token.callback_confirmed, 'true')
        self.token.set_callback(None)
        self.assertEqual(self.token.callback, None)
        # TODO: The following test should probably not pass, but it does
        #       To fix this, check for None and unset 'true' in set_callback
        #       Additionally, should a confirmation truly be done of the callback?
        self.assertEqual(self.token.callback_confirmed, 'true')

    def test_set_verifier(self):
        self.assertEqual(self.token.verifier, None)
        v = oauth.generate_verifier()
        self.token.set_verifier(v)
        self.assertEqual(self.token.verifier, v)
        self.token.set_verifier()
        self.assertNotEqual(self.token.verifier, v)
        self.token.set_verifier('')
        self.assertEqual(self.token.verifier, '')

    def test_get_callback_url(self):
        self.assertEqual(self.token.get_callback_url(), None)

        self.token.set_verifier()
        self.assertEqual(self.token.get_callback_url(), None)

        cb = 'http://www.example.com/my-callback?save=1&return=true'
        v = oauth.generate_verifier()
        self.token.set_callback(cb)
        self.token.set_verifier(v)
        url = self.token.get_callback_url()
        verifier_str = '&oauth_verifier=%s' % v
        self.assertEqual(url, '%s%s' % (cb, verifier_str))

        cb = 'http://www.example.com/my-callback-no-query'
        v = oauth.generate_verifier()
        self.token.set_callback(cb)
        self.token.set_verifier(v)
        url = self.token.get_callback_url()
        verifier_str = '?oauth_verifier=%s' % v
        self.assertEqual(url, '%s%s' % (cb, verifier_str))

    def test_to_string(self):
        string = 'oauth_token_secret=%s&oauth_token=%s' % (self.secret,
                                                           self.key)
        self.assertEqual(self.token.to_string(), string)

        self.token.set_callback('http://www.example.com/my-callback')
        string += '&oauth_callback_confirmed=true'
        self.assertEqual(self.token.to_string(), string)

    def _compare_tokens(self, new):
        self.assertEqual(self.token.key, new.key)
        self.assertEqual(self.token.secret, new.secret)
        # TODO: What about copying the callback to the new token?
        # self.assertEqual(self.token.callback, new.callback)
        self.assertEqual(self.token.callback_confirmed,
                         new.callback_confirmed)
        # TODO: What about copying the verifier to the new token?
        # self.assertEqual(self.token.verifier, new.verifier)

    def test_to_string(self):
        tok = oauth.Token('tooken', 'seecret')
        self.assertEqual(str(tok), 'oauth_token_secret=seecret&oauth_token=tooken')

    def test_from_string(self):
        self.assertRaises(ValueError, lambda: oauth.Token.from_string(''))
        self.assertRaises(ValueError, lambda: oauth.Token.from_string('blahblahblah'))
        self.assertRaises(ValueError, lambda: oauth.Token.from_string('blah=blah'))

        self.assertRaises(ValueError, lambda: oauth.Token.from_string('oauth_token_secret=asfdasf'))
        self.assertRaises(ValueError, lambda: oauth.Token.from_string('oauth_token_secret='))
        self.assertRaises(ValueError, lambda: oauth.Token.from_string('oauth_token=asfdasf'))
        self.assertRaises(ValueError, lambda: oauth.Token.from_string('oauth_token='))
        self.assertRaises(ValueError, lambda: oauth.Token.from_string('oauth_token=&oauth_token_secret='))
        self.assertRaises(ValueError, lambda: oauth.Token.from_string('oauth_token=tooken%26oauth_token_secret=seecret'))

        string = self.token.to_string()
        new = oauth.Token.from_string(string)
        self._compare_tokens(new)

        self.token.set_callback('http://www.example.com/my-callback')
        string = self.token.to_string()
        new = oauth.Token.from_string(string)
        self._compare_tokens(new)

class TestRequest(unittest.TestCase):
    pass

class TestServer(unittest.TestCase):
    pass

class TestClient(unittest.TestCase):
    pass

class TestDataStore(unittest.TestCase):
    pass

class TestSignatureMethod(unittest.TestCase):
    pass

class TestSignatureMethod_HMAC_SHA1(unittest.TestCase):
    pass

class TestSignatureMethod_PLAINTEXT(unittest.TestCase):
    pass

