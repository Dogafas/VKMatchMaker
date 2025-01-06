CREATE TABLE public.users (
	id serial4 NOT NULL,
	vk_user_id int4 NOT NULL,
	first_name varchar(255) NULL,
	last_name varchar(255) NULL,
	city varchar(255) NULL,
	created_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	search_offset int4 DEFAULT 0 NULL,
	last_viewed_result_id int4 NULL,
	CONSTRAINT users_pkey PRIMARY KEY (id),
	CONSTRAINT users_vk_user_id_key UNIQUE (vk_user_id)
);


CREATE TABLE public.search_results (
	id serial4 NOT NULL,
	user_id int4 NULL,
	vk_search_user_id int4 NOT NULL,
	first_name varchar(255) NULL,
	last_name varchar(255) NULL,
	profile_url varchar(255) NULL,
	is_blacklisted bool DEFAULT false NULL,
	created_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT search_results_pkey PRIMARY KEY (id),
	CONSTRAINT search_results_user_id_vk_search_user_id_key UNIQUE (user_id, vk_search_user_id),
	CONSTRAINT search_results_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);


CREATE TABLE public.blacklisted_users (
	id serial4 NOT NULL,
	user_id int4 NULL,
	vk_blacklisted_user_id int4 NOT NULL,
	profile_url varchar(255) NULL,
	created_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT blacklisted_users_pkey PRIMARY KEY (id),
	CONSTRAINT blacklisted_users_user_id_vk_blacklisted_user_id_key UNIQUE (user_id, vk_blacklisted_user_id),
	CONSTRAINT blacklisted_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);