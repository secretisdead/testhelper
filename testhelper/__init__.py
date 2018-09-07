import unittest
import uuid
from datetime import datetime, timezone

from base64_url import base64_url_encode, base64_url_decode

def compare_base_attributes(object1, object2):
	# check if all int, string, and bool properties of two objects are equal
	for attr, value in object1.__dict__.items():
		if (
				isinstance(value, int)
				or isinstance(value, str)
				or isinstance(value, bool)
			):
			if value != getattr(object2, attr):
				return False
	return True

invalid_ids = [
	'not a valid base64_url string',
	'invalid_padding_for_base64_url_id',
	1,
	# some search methods accept lists of ids so the string value here is also
	# an invalid id, but lists in general aren't valid ids
	['not a valid base64_url string'],
	{'dict': 'ionary'},
]
valid_ints = [
	# valid int
	1,
	2,
	3,
	# valid but non-int
	1.1,
	0.1,
]
invalid_ints = [
	'string',
	b'',
	['list'],
	{'dict': 'ionary'},
]
invalid_timestamps = [
	'string',
	['list'],
	{'dict': 'ionary'},
]
truthy_values = [
	True,
	'non-empty string',
	['non-empty list'],
	{'non-empty': 'dict'},
]
falsy_values = [
	False,
	'',
	[],
	{},
	None,
]
invalid_remote_origins = [
	'not a valid ip address string',
	['list'],
	{'dict': 'ionary'},
]
invalid_group_bits = [
	'string',
	['list'],
	{'dict': 'ionary'},
]
invalid_strings = []

class TestHelper(unittest.TestCase):
	def assert_invalid_id_raises(self, f):
		# id must be a base64_url string or bytes-like
		for invalid_id in invalid_ids:
			with self.assertRaises(Exception):
				f(invalid_id)

	def assert_invalid_id_returns_none(self, f):
		# id must be a base64_url string or bytes-like
		for invalid_id in [
				'not a valid base64_url string',
				'invalid_padding_for_base64_url_id',
				1,
				[],
				{},
				['list'],
				{'dict': 'ionary'},
			]:
			self.assertEqual(None, f(invalid_id))

	def assert_invalid_int_raises(self, f):
		# input is cast to int so anything that doesn't cast to int should raise
		for invalid_int in invalid_ints:
			with self.assertRaises(Exception):
				f(invalid_int)

	def assert_invalid_timestamp_raises(self, f):
		# input is cast to int and also fed to datetime.fromtimestamp so anything
		# that doesn't cast to int or that isn't accepted by datetime.fromtimestamp
		# should raise
		for invalid_timestamp in invalid_timestamps:
			with self.assertRaises(Exception):
				f(invalid_timestamp)

	def assert_invalid_string_raises(self, f):
		# input is cast to string so anything that doesn't cast gracefully
		# to string should raise
		#TODO most objects cast gracefully to a string representation
		#TODO are there python objects that raise when casting to string?
		for invalid_string in invalid_strings:
			with self.assertRaises(Exception):
				f(invalid_string)

	def class_create_get_and_defaults(self, class_name, create, get, defaults):
		# instantiate directly
		instance = class_name()
		# create in db
		object = create()
		self.assertIsInstance(object, class_name)
		# objects can be retrieved by both id and id_bytes
		self.assertTrue(
			compare_base_attributes(
				get(object.id),
				get(object.id_bytes),
			)
		)
		# fetched object should be the same as the one returned from create
		self.assertTrue(
			compare_base_attributes(object, get(object.id))
		)
		# default values should match
		for property, value in defaults.items():
			self.assertEqual(value, getattr(instance, property))
			self.assertEqual(value, getattr(object, property))

	def id_property(self, class_name, create, property):
		# id can be specified from bytes-like
		expected_id_bytes = uuid.uuid4().bytes
		expected_id = base64_url_encode(expected_id_bytes)
		# instantiate directly
		instance = class_name(**{property: expected_id_bytes})
		instance_id_bytes = getattr(instance, property + '_bytes')
		instance_id = getattr(instance, property)
		self.assertEqual(expected_id_bytes, instance_id_bytes)
		self.assertEqual(expected_id, instance_id)
		# create in db
		object = create(**{property: expected_id_bytes})
		object_id_bytes = getattr(object, property + '_bytes')
		object_id = getattr(object, property)
		self.assertEqual(expected_id_bytes, object_id_bytes)
		self.assertEqual(expected_id, object_id)

		# id can be specified from a base64_url string
		expected_id_bytes = uuid.uuid4().bytes
		expected_id = base64_url_encode(expected_id_bytes)
		# instantiate directly
		instance = class_name(**{property: expected_id})
		instance_id_bytes = getattr(instance, property + '_bytes')
		instance_id = getattr(instance, property)
		self.assertEqual(expected_id_bytes, instance_id_bytes)
		self.assertEqual(expected_id, instance_id)
		# create in db
		object = create(**{property: expected_id})
		object_id_bytes = getattr(object, property + '_bytes')
		object_id = getattr(object, property)
		self.assertEqual(expected_id_bytes, object_id_bytes)
		self.assertEqual(expected_id, object_id)

		self.assert_invalid_id_raises(
			lambda input: class_name(**{property: input})
		)
		self.assert_invalid_id_raises(
			lambda input: create(**{property: input})
		)

	def int_property(self, class_name, create, property):
		for valid_int in valid_ints:
			# int properties first cast to int
			# so shouldn't raise on valid input, but should only result in ints
			valid_int = int(valid_int)

			# instantiate directly
			instance = class_name(
				**{property: valid_int}
			)
			instance_int = getattr(instance, property)
			self.assertEqual(valid_int, instance_int)

			# create in db
			object = create(**{property: valid_int})
			object_int = getattr(object, property)
			self.assertEqual(valid_int, object_int)

		self.assert_invalid_int_raises(
			lambda input: class_name(**{property: input})
		)
		self.assert_invalid_int_raises(
			lambda input: create(**{property: input})
		)

	def time_property(self, class_name, create, property):
		for valid_timestamp in [
				# valid int
				0,
				1111111111,
				1234567890,
				-1,
				# valid but non-int
				0.1,
				1111111111.12345,
				1234567890.12345,
				-1.1,
			]:
			# time properties first cast to int then use datetime.fromtimestamp
			# so shouldn't raise on valid input, but should only result in ints
			valid_timestamp = int(valid_timestamp)
			expected_datetime = datetime.fromtimestamp(
				valid_timestamp,
				timezone.utc,
			)

			# instantiate directly
			instance = class_name(
				**{property + '_time': valid_timestamp}
			)
			instance_time = getattr(instance, property + '_time')
			instance_datetime = getattr(
				instance, property + '_datetime'
			)
			self.assertEqual(valid_timestamp, instance_time)
			self.assertEqual(expected_datetime, instance_datetime)

			# create in db
			object = create(**{property + '_time': valid_timestamp})
			object_time = getattr(object, property + '_time')
			object_datetime = getattr(object, property + '_datetime')
			self.assertEqual(valid_timestamp, object_time)
			self.assertEqual(expected_datetime, object_datetime)

		self.assert_invalid_timestamp_raises(
			lambda input: class_name(**{property + '_time': input})
		)
		self.assert_invalid_timestamp_raises(
			lambda input: create(**{property + '_time': input})
		)

	def bool_property(self, class_name, create, property):
		# bool properties are evaluated to truthy or falsy, so there aren't
		# any invalid inputs, just what they're interpreted as
		truthy_inputs = [
			True,
			'non-empty string',
			['non-empty list'],
			{'non-empty': 'dict'},
		]
		for truthy_input in truthy_inputs:
			# instantiate directly
			instance = class_name(
				**{property: truthy_input}
			)
			self.assertEqual(True, getattr(instance, property))

			# create in db
			object = create(**{property: truthy_input})
			self.assertEqual(True, getattr(object, property))

		falsy_inputs = [False, '', [], {}, None]
		for falsy_input in falsy_inputs:
			# instantiate directly
			instance = class_name(
				**{property: falsy_input}
			)
			self.assertEqual(False, getattr(instance, property))

			# create in db
			object = create(**{property: falsy_input})
			self.assertEqual(False, getattr(object, property))

	def string_property(self, class_name, create, property):
		for valid_string in [
				# valid string
				'some string',
				# valid but non-strings
				1,
				0.1,
				[],
				{},
				['list'],
				{'dict': 'ionary'},
			]:
			# string properties first cast to string
			# so shouldn't raise on valid input, but should only result in strings
			valid_string = str(valid_string)

			# instantiate directly
			instance = class_name(
				**{property: valid_string}
			)
			instance_string = getattr(instance, property)
			self.assertEqual(valid_string, instance_string)

			# create in db
			object = create(**{property: valid_string})
			object_string = getattr(object, property)
			self.assertEqual(valid_string, object_string)

		self.assert_invalid_string_raises(
			lambda input: class_name(**{property: input})
		)
		self.assert_invalid_string_raises(
			lambda input: create(**{property: input})
		)

	def delete(self, create, get, delete):
		# by id
		object = create()
		self.assertIsNotNone(get(object.id))
		delete(object.id)
		self.assertIsNone(get(object.id))
		# by id_bytes
		object = create()
		self.assertIsNotNone(get(object.id))
		delete(object.id_bytes)
		self.assertIsNone(get(object.id))

		self.assert_invalid_id_raises(delete)

	def id_collision(self, create):
		object = create()
		# by id
		with self.assertRaises(Exception):
			create(id=object.id)
		# by id_bytes
		with self.assertRaises(Exception):
			create(id=object.id_bytes)

	def count(self, create, count, delete):
		object1 = create()
		object2 = create()
		self.assertEqual(2, count())

		delete(object2.id)
		self.assertEqual(1, count())

		object3 = create()
		self.assertEqual(2, count())

		delete(object3.id)
		self.assertEqual(1, count())

		delete(object1.id)
		self.assertEqual(0, count())

	def search(self, create, search, delete):
		object1 = create()
		object2 = create()
		objects = search()
		self.assertTrue(object1 in objects)
		self.assertTrue(object2 in objects)

		delete(object2.id)
		objects = search()
		self.assertTrue(object1 in objects)
		self.assertTrue(object2 not in objects)

		object3 = create()
		objects = search()
		self.assertTrue(object1 in objects)
		self.assertTrue(object2 not in objects)
		self.assertTrue(object3 in objects)

		delete(object3.id)
		objects = search()
		self.assertTrue(object1 in objects)
		self.assertTrue(object2 not in objects)
		self.assertTrue(object3 not in objects)

		delete(object1.id)
		objects = search()
		self.assertTrue(object1 not in objects)
		self.assertTrue(object2 not in objects)
		self.assertTrue(object3 not in objects)

	def search_sort_order_and_pagination(
			self,
			create,
			column_field,
			search,
			first_value=1,
			middle_value=2,
			last_value=3,
		):
		object_first = create(**{column_field: first_value})
		object_middle = create(**{column_field: middle_value})
		object_last = create(**{column_field: last_value})

		# ascending
		ascending_objects = [
			object_first,
			object_middle,
			object_last,
		]
		objects = search(sort=column_field, order='asc')
		for object in ascending_objects:
			self.assertTrue(
				compare_base_attributes(
					object,
					objects.values()[ascending_objects.index(object)],
				)
			)
		for page in range(4):
			objects = search(sort=column_field, order='asc', perpage=1, page=page)
			for object in ascending_objects:
				if ascending_objects.index(object) != page:
					self.assertTrue(object not in objects)
				else:
					self.assertTrue(object in objects)

		# descending
		descending_objects = [
			object_last,
			object_middle,
			object_first,
		]
		objects = search(sort=column_field, order='desc')
		for object in descending_objects:
			self.assertTrue(
				compare_base_attributes(
					object,
					objects.values()[descending_objects.index(object)],
				)
			)
		for page in range(4):
			objects = search(sort=column_field, order='desc', perpage=1, page=page)
			for object in descending_objects:
				if descending_objects.index(object) != page:
					self.assertTrue(object not in objects)
				else:
					self.assertTrue(object in objects)

	def search_by_id(
			self,
			create,
			column_field,
			search,
			filter_field,
			id1=None,
			id2=None,
		):
		if not id1:
			id1 = base64_url_encode(uuid.uuid4().bytes)
		if not id2:
			id2 = base64_url_encode(uuid.uuid4().bytes)

		object1 = create(**{column_field: id1})
		object2 = create(**{column_field: id2})

		objects = search(
			filter={filter_field: id1}
		)
		self.assertTrue(object1 in objects)
		self.assertTrue(object2 not in objects)

		objects = search(
			filter={filter_field: id2}
		)
		self.assertTrue(object1 not in objects)
		self.assertTrue(object2 in objects)

		objects = search(
			filter={
				filter_field: [
					id1,
					id2,
				]
			}
		)
		self.assertTrue(object1 in objects)
		self.assertTrue(object2 in objects)

		# invalid filter exceptions are consumed by the statement helper
		# so invalid values accompanied by valid values behave normally
		objects = search(filter={filter_field: invalid_ids + [id1]})
		self.assertTrue(object1 in objects)
		self.assertTrue(object2 not in objects)
		for invalid_id in invalid_ids:
			objects = search(filter={filter_field: [invalid_id, id1]})
			self.assertTrue(object1 in objects)
			self.assertTrue(object2 not in objects)
		# for safety a filter with only invalid values should return no results
		objects = search(filter={filter_field: invalid_ids})
		self.assertEqual(0, len(objects))
		for invalid_id in invalid_ids:
			objects = search(filter={filter_field: invalid_id})
			self.assertEqual(0, len(objects))

	def search_by_int_cutoff(
			self,
			create,
			column_field,
			search,
			filter_field_less_than,
			filter_field_greater_than,
			first_value=0,
			middle_value=1,
			last_value=2,
			invalid_values=invalid_ints,
		):
		object_first = create(**{column_field: first_value})
		object_middle = create(**{column_field: middle_value})
		object_last = create(**{column_field: last_value})

		objects = search(
			filter={filter_field_less_than: last_value}
		)
		self.assertEqual(2, len(objects))
		self.assertTrue(object_first in objects)
		self.assertTrue(object_middle in objects)
		self.assertTrue(object_last not in objects)

		objects = search(
			filter={filter_field_less_than: middle_value}
		)
		self.assertEqual(1, len(objects))
		self.assertTrue(object_first in objects)
		self.assertTrue(object_middle not in objects)
		self.assertTrue(object_last not in objects)

		objects = search(filter={filter_field_less_than: first_value})
		self.assertEqual(0, len(objects))

		objects = search(filter={filter_field_greater_than: first_value})
		self.assertEqual(2, len(objects))
		self.assertTrue(object_first not in objects)
		self.assertTrue(object_middle in objects)
		self.assertTrue(object_last in objects)

		objects = search(
			filter={filter_field_greater_than: middle_value}
		)
		self.assertEqual(1, len(objects))
		self.assertTrue(object_first not in objects)
		self.assertTrue(object_middle not in objects)
		self.assertTrue(object_last in objects)

		objects = search(
			filter={filter_field_greater_than: last_value}
		)
		self.assertEqual(0, len(objects))

		objects = search(
			filter={
				filter_field_greater_than: first_value,
				filter_field_less_than: last_value,
			}
		)
		self.assertEqual(1, len(objects))
		self.assertTrue(object_first not in objects)
		self.assertTrue(object_middle in objects)
		self.assertTrue(object_last not in objects)

		# invalid filter exceptions are aborted by the statement helper
		# so invalid values return no results
		for invalid_value in invalid_values:
			objects = search(filter={filter_field_greater_than: invalid_value})
			self.assertEqual(0, len(objects))
			objects = search(filter={filter_field_less_than: invalid_value})
			self.assertEqual(0, len(objects))

	def search_by_time_cutoff(
			self,
			create,
			column_field,
			search,
			filter_field,
		):
		self.search_by_int_cutoff(
			create,
			column_field,
			search,
			filter_field + '_before',
			filter_field + '_after',
			invalid_values=invalid_timestamps,
		)

	def search_by_string_like(
			self,
			create,
			column_field,
			search,
			filter_field,
		):
		object_foo = create(**{column_field: 'foo'})
		object_bar = create(**{column_field: 'bar'})
		object_baz = create(**{column_field: 'baz'})

		objects = search(filter={filter_field: 'foo'})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar not in objects)
		self.assertTrue(object_baz not in objects)

		objects = search(filter={filter_field: 'bar'})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz not in objects)

		objects = search(filter={filter_field: 'ba%'})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz in objects)

		objects = search(filter={filter_field: 'bat'})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar not in objects)
		self.assertTrue(object_baz not in objects)

		objects = search(filter={filter_field: ['foo', 'bar']})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz not in objects)

		# invalid filter exceptions are aborted by the statement helper
		# so any invalid value should return no results

		# but since string filters are cast to string before the query they
		# should always be valid
		pass

	def search_by_string_not_like(
			self,
			create,
			column_field,
			search,
			filter_field,
		):
		object_foo = create(**{column_field: 'foo'})
		object_bar = create(**{column_field: 'bar'})
		object_baz = create(**{column_field: 'baz'})

		objects = search(filter={filter_field: 'foo'})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz in objects)

		objects = search(filter={filter_field: 'bar'})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar not in objects)
		self.assertTrue(object_baz in objects)

		objects = search(filter={filter_field: 'ba%'})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar not in objects)
		self.assertTrue(object_baz not in objects)

		objects = search(filter={filter_field: 'bat'})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar not in objects)
		self.assertTrue(object_baz not in objects)

		objects = search(filter={filter_field: ['foo', 'bar']})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz in objects)

		# invalid filter exceptions are consumed by the statement helper
		# so invalid values accompanied by valid values behave normally
		objects = search(filter={filter_field: invalid_strings + ['foo']})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz in objects)
		for invalid_string in invalid_strings:
			objects = search(filter={filter_field: [invalid_string, 'foo']})
			self.assertTrue(object_foo not in objects)
			self.assertTrue(object_bar in objects)
			self.assertTrue(object_baz in objects)

		# for safety a filter with only invalid values should return no results

		# but since string filters are cast to string before the query they
		# should always be valid
		pass

	def search_by_string_equal(
			self,
			create,
			column_field,
			search,
			filter_field,
		):
		object_foo = create(**{column_field: 'foo'})
		object_bar = create(**{column_field: 'bar'})
		object_baz = create(**{column_field: 'baz'})

		objects = search(filter={filter_field: 'foo'})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar not in objects)
		self.assertTrue(object_baz not in objects)

		objects = search(filter={filter_field: 'bar'})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz not in objects)

		objects = search(filter={filter_field: 'baz'})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar not in objects)
		self.assertTrue(object_baz in objects)

		objects = search(filter={filter_field: 'bat'})
		self.assertEqual(0, len(objects))

		objects = search(filter={filter_field: ['foo', 'bar']})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz not in objects)

		# invalid filter exceptions are aborted by the statement helper
		# so any invalid values should return no results

		# but since string filters are cast to string before the query they
		# should always be valid
		pass

	def search_by_string_not_equal(
			self,
			create,
			column_field,
			search,
			filter_field,
		):
		object_foo = create(**{column_field: 'foo'})
		object_bar = create(**{column_field: 'bar'})
		object_baz = create(**{column_field: 'baz'})

		objects = search(filter={filter_field: 'foo'})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz in objects)

		objects = search(filter={filter_field: 'bar'})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar not in objects)
		self.assertTrue(object_baz in objects)

		objects = search(filter={filter_field: 'baz'})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz not in objects)

		objects = search(filter={filter_field: 'bat'})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz in objects)

		objects = search(filter={filter_field: ['foo', 'bar']})
		self.assertTrue(object_foo in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz in objects)

		# invalid filter exceptions are consumed by the statement helper
		# so invalid values accompanied by valid values behave normally
		objects = search(filter={filter_field: invalid_strings + ['foo']})
		self.assertTrue(object_foo not in objects)
		self.assertTrue(object_bar in objects)
		self.assertTrue(object_baz in objects)
		for invalid_string in invalid_strings:
			objects = search(filter={filter_field: [invalid_string, 'foo']})
			self.assertTrue(object_foo not in objects)
			self.assertTrue(object_bar in objects)
			self.assertTrue(object_baz in objects)

		# for safety a filter with only invalid values should return no results

		# but since string filters are cast to string before the query they
		# should always be valid
		pass

	def search_by_bool(self, create, column_field, search, filter_field):
		object_true = create(**{column_field: 1})
		object_false = create(**{column_field: 0})

		objects = search(filter={filter_field: True})
		self.assertTrue(object_true in objects)
		self.assertTrue(object_false not in objects)

		objects = search(filter={filter_field: False})
		self.assertTrue(object_true not in objects)
		self.assertTrue(object_false in objects)

		# bool filters are evaluated to truthy or falsy, so there aren't
		# any invalid inputs, just what they're interpreted as
		for truthy_value in truthy_values:
			objects = search(filter={filter_field: truthy_value})
			self.assertTrue(object_true in objects)
			self.assertTrue(object_false not in objects)
		for falsy_value in falsy_values:
			objects = search(filter={filter_field: falsy_value})
			self.assertTrue(object_true not in objects)
			self.assertTrue(object_false in objects)

	def search_by_remote_origin(
			self,
			create,
			column_field,
			search,
			filter_field,
		):
		remote_origin1 = '1.1.1.1'
		remote_origin2 = '2.2.2.2'
		object1 = create(**{column_field: remote_origin1})
		object2 = create(**{column_field: remote_origin1})
		object3 = create(**{column_field: remote_origin2})

		for filter_prefix, assert_ in [
				('with_', self.assertTrue),
				('without_', self.assertFalse),
			]:
			objects = search(
				filter={filter_prefix + filter_field: remote_origin1},
			)
			assert_(object1 in objects)
			assert_(object2 in objects)
			assert_(object3 not in objects)

			objects = search(
				filter={filter_prefix + filter_field: remote_origin2},
			)
			assert_(object1 not in objects)
			assert_(object2 not in objects)
			assert_(object3 in objects)

			# multiple values match if any target is satisfied on with
			# multiple values match if all targets are satisfied on without
			objects = search(
				filter={
					filter_prefix + filter_field: [remote_origin1, remote_origin2],
				},
			)
			assert_(object1 in objects)
			assert_(object2 in objects)
			assert_(object3 in objects)

			# for safety a filter with only invalid values should return no results
			objects = search(
				filter={filter_prefix + filter_field: invalid_remote_origins},
			)
			self.assertEqual(0, len(objects))
			for invalid_value in invalid_remote_origins:
				objects = search(
					filter={filter_prefix + filter_field: invalid_value},
				)
				self.assertEqual(0, len(objects))

		# with
		# invalid filter exceptions are aborted by the statement helper
		# so any invalid values should return no results
		objects = search(
			filter={
				'with_' + filter_field: invalid_remote_origins + [remote_origin1],
			},
		)
		self.assertTrue(object1 not in objects)
		self.assertTrue(object2 not in objects)
		self.assertTrue(object3 not in objects)
		for invalid_value in invalid_remote_origins:
			objects = search(
				filter={
					'with_' + filter_field: [invalid_value, remote_origin1],
				},
			)
			self.assertTrue(object1 not in objects)
			self.assertTrue(object2 not in objects)
			self.assertTrue(object3 not in objects)

		# without
		# invalid filter exceptions are consumed by the statement helper
		# so invalid values accompanied by valid values behave normally
		objects = search(
			filter={
				'without_' + filter_field: (
					invalid_remote_origins + [remote_origin1]
				),
			},
		)
		self.assertTrue(object1 not in objects)
		self.assertTrue(object2 not in objects)
		self.assertTrue(object3 in objects)
		for invalid_value in invalid_remote_origins:
			objects = search(
				filter={
					'without_' + filter_field: [invalid_value, remote_origin1],
				},
			)
			self.assertTrue(object1 not in objects)
			self.assertTrue(object2 not in objects)
			self.assertTrue(object3 in objects)

	def search_by_group_bits(self, create, search):
		group1_bit = 1
		group2_bit = 2
		group3_bit = 4
		group4_bit = 8
		group1_and_group3_bits = 5
		group2_and_group3_bits = 6

		object_group1 = create(group_bits=group1_bit)
		object_group2 = create(group_bits=group2_bit)
		object_group3 = create(group_bits=group3_bit)

		object_group1_and_group3 = create(
			group_bits=group1_and_group3_bits,
		)
		object_group2_and_group3 = create(
			group_bits=group2_and_group3_bits,
		)

		for filter_prefix, assert_ in [
				('with_', self.assertTrue),
				('without_', self.assertFalse),
			]:
			objects = search(filter={filter_prefix + 'group_bits': group1_bit})
			assert_(object_group1 in objects)
			assert_(object_group2 not in objects)
			assert_(object_group3 not in objects)
			assert_(object_group1_and_group3 in objects)
			assert_(object_group2_and_group3 not in objects)

			objects = search(filter={filter_prefix + 'group_bits': group2_bit})
			assert_(object_group1 not in objects)
			assert_(object_group2 in objects)
			assert_(object_group3 not in objects)
			assert_(object_group1_and_group3 not in objects)
			assert_(object_group2_and_group3 in objects)

			objects = search(filter={filter_prefix + 'group_bits': group3_bit})
			assert_(object_group1 not in objects)
			assert_(object_group2 not in objects)
			assert_(object_group3 in objects)
			assert_(object_group1_and_group3 in objects)
			assert_(object_group2_and_group3 in objects)

			objects = search(filter={filter_prefix + 'group_bits': group4_bit})
			assert_(object_group1 not in objects)
			assert_(object_group2 not in objects)
			assert_(object_group3 not in objects)
			assert_(object_group1_and_group3 not in objects)
			assert_(object_group2_and_group3 not in objects)

		# invalid filter exceptions are aborted by the statement helper
		# so invalid values return no results
		for invalid_value in invalid_group_bits:
			objects = search(filter={'with_group_bits': invalid_value})
			self.assertEqual(0, len(objects))
			self.assertTrue(object_group1 not in objects)
			self.assertTrue(object_group2 not in objects)
			self.assertTrue(object_group3 not in objects)
			self.assertTrue(object_group1_and_group3 not in objects)
			self.assertTrue(object_group2_and_group3 not in objects)

		# for safety a filter with only invalid values should return no results
		for invalid_value in invalid_group_bits:
			objects = search(filter={'with_group_bits': invalid_value})
			self.assertEqual(0, len(objects))

		# invalid filter exceptions are consumed by the statement
		# helper, so invalid values are ignored
		for invalid_value in invalid_group_bits:
			objects = search(filter={'without_group_bits': invalid_value})
			self.assertEqual(5, len(objects))
			self.assertTrue(object_group1 in objects)
			self.assertTrue(object_group2 in objects)
			self.assertTrue(object_group3 in objects)
			self.assertTrue(object_group1_and_group3 in objects)
			self.assertTrue(object_group2_and_group3 in objects)


